'''
Created on Dec 16, 2010

@author: karmel
'''
from glasslab.config import current_settings
from glasslab.glassatlas.datatypes.transcript import TranscriptBase, MAX_GAP
from glasslab.sequencing.datatypes.tag import multiprocess_glass_tags,\
    wrap_errors
from glasslab.utils.database import execute_query

def wrap_add_transcripts_from_rnaseq(cls, chr_list, *args): wrap_errors(cls._add_transcripts_from_rnaseq, chr_list, *args)

class GlassTranscribedRna(TranscriptBase):
    '''
    Transcribed RNA sequenced in RNA-Seq experiments.
    '''
    ucsc_session_url = 'http%3A%2F%2Fbiowhat.ucsd.edu%2Fkallison%2Fucsc%2Fsessions%2Fglass_transcribed_rna_'
    
    class Meta:
        db_table    = 'glass_atlas_%s"."glass_transcribed_rna' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcribed_RNA'
        verbose_name= 'Transcribed RNA'
    
    ################################################
    # RNA-Seq to transcripts
    ################################################            
    @classmethod 
    def add_tags_from_rnaseq(cls,  tag_table, sequencing_run):
        multiprocess_glass_tags(wrap_add_transcripts_from_rnaseq, cls, sequencing_run)
        
    @classmethod
    def _add_transcripts_from_rnaseq(cls, chr_list, sequencing_run):
        for chr_id in chr_list:
            print 'Adding transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s.save_transcripts_from_sequencing_run(%d, %d,'%s', %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       sequencing_run.id, chr_id, 
                       sequencing_run.source_table.strip(), MAX_GAP)
            execute_query(query)
            
    