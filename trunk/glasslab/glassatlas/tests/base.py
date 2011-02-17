'''
Created on Jan 4, 2011

@author: karmel
'''
import unittest
from glasslab.config import current_settings
from glasslab.utils.database import execute_query
from glasslab.glassatlas.sql.generate_transcript_table_sql import sql as transcript_table_sql
from glasslab.glassatlas.sql.generate_transcribed_rna_table_sql import sql as transcribed_rna_table_sql
from glasslab.glassatlas.sql.generate_feature_table_sql import sql as features_table_sql
from glasslab.glassatlas.sql.transcripts_from_tags_functions import sql as transcript_function_sql
from glasslab.glassatlas.sql.transcribed_rna_from_tags_functions import sql as transcribed_rna_function_sql
from glasslab.glassatlas.sql.features_functions import sql as features_function_sql
from glasslab.sequencing.datatypes.tag import GlassTag
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from glasslab.glassatlas.datatypes.metadata import SequencingRun
from django.db import connection
from random import randint

class GlassTestCase(unittest.TestCase):
    '''
    Base TestCase capable of setting up and taking down the test DB.
    '''
    set_up_db = True
    test_genome = 'test'
    test_cell_type = 'thiomac'
    cell_base = None
    sequencing_runs = None # Run records created that should be deleted
    
    def setUp(self):
        '''
        Sets up test DB and runs all table and function create statements.
        '''
        # Set the schema name
        current_settings.TRANSCRIPT_GENOME = self.test_genome
        current_settings.CURRENT_CELL_TYPE = self.test_cell_type
        current_settings.CURRENT_SCHEMA = 'glass_atlas_%s_%s' % (current_settings.TRANSCRIPT_GENOME, 
                                                                 current_settings.CURRENT_CELL_TYPE)
        
        self.sequencing_runs = []
        
        if self.set_up_db:
            execute_query('CREATE SCHEMA %s' % current_settings.CURRENT_SCHEMA)
    
            for func in (transcript_table_sql, transcribed_rna_table_sql,
                         features_table_sql,
                         transcript_function_sql, transcribed_rna_function_sql,
                         features_function_sql):
                execute_query(func(current_settings.TRANSCRIPT_GENOME, 
                                   current_settings.CURRENT_CELL_TYPE))
        
        self.cell_base = CellTypeBase().get_cell_type_base(current_settings.CURRENT_CELL_TYPE)()     
        self.cell_base.glass_transcript.turn_off_autovacuum()
        
        # Reset variables
        current_settings.CHR_LISTS = None
            
    def tearDown(self):
        '''
        Delete functions, tables, etc.
        '''
        for run in self.sequencing_runs:
            run.delete()
            
        execute_query('''SELECT setval('"%s_id_seq"', 
                            (SELECT MAX(id) FROM "%s"), true);''' 
                                % (SequencingRun._meta.db_table, SequencingRun._meta.db_table)) 
        
        execute_query('DROP SCHEMA %s CASCADE' % current_settings.CURRENT_SCHEMA)
        
    def create_tag_table(self, sequencing_run_name='', sequencing_run_type='Gro-Seq'):
        '''
        Can be called in order to create tag tables (split by chromosome)
        for the passed run name.
        '''
        GlassTag.create_parent_table(sequencing_run_name)
        GlassTag.create_partition_tables()
        GlassTag.add_indices()
        self.sequencing_runs.append(GlassTag.add_record_of_tags(description='Created during a unit test.', 
                                                                type=sequencing_run_type, standard=True))
        connection.close()
        
    def _create_transcript(self, chr, strand, start, end):
        # Create corresponding transcript for exon/ncRNA stitching, association
        source_table = 'sample_transcript_run_%d' % randint(0,10000)
        self.create_tag_table(sequencing_run_name=source_table, sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        return source_table