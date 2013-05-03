'''
Created on Sep 27, 2010

@author: karmel
'''
from __future__ import division
from django.db import models, connection
from vespucci.genomereference.datatypes import Chromosome, SequencingRun
from vespucci.config import current_settings
from vespucci.utils.datatypes.basic_model import DynamicTable, Int8RangeField
from vespucci.utils.database import execute_query
from vespucci.atlas.datatypes.transcript import multiprocess_all_chromosomes,\
    wrap_errors

    
def wrap_partition_tables(cls, chr_list): 
    wrap_errors(cls._create_partition_tables, chr_list)
def wrap_translate_from_prep(cls, chr_list): 
    wrap_errors(cls._translate_from_prep, chr_list)
def wrap_set_refseq(cls, chr_list): 
    wrap_errors(cls._set_refseq, chr_list)
def wrap_insert_matching_tags(cls, chr_list): 
    wrap_errors(cls._insert_matching_tags, chr_list)
def wrap_add_indices(cls, chr_list): 
    wrap_errors(cls._add_indices, chr_list)        
    
class AtlasTag(DynamicTable):
    '''
    Denormalized version of tag input::
        
        strand    chr    start            sequence_matched
        -       chr5    66529332        ATTAGTTGACAGGAATTAGCTAGGAACCACAGAA

    
    '''
    prep_table = None
    
    chromosome = models.ForeignKey(Chromosome)
    strand = models.IntegerField(max_length=1)
    start = models.IntegerField(max_length=12)
    end = models.IntegerField(max_length=12)
    
    start_end = Int8RangeField(max_length=255, null=True)
    
    refseq = models.NullBooleanField(default=None)
    
     
    @classmethod        
    def create_prep_table(cls, name):
        '''
        Create table that will be used for to upload preparatory tag information,
        dynamically named.
        '''
        cls.set_prep_table('prep_%s' % name)
        table_sql = """
        CREATE TABLE "%s" (
            strand_char character(1) default NULL,
            chromosome varchar(20),
            "start" bigint,
            sequence_matched varchar(100)
        );
        """ % cls.prep_table
        execute_query(table_sql)
    
    @classmethod 
    def set_prep_table(cls, name): 
        cls.prep_table = '%s"."%s' % (current_settings.CURRENT_SCHEMA, name)
    
    @classmethod        
    def delete_prep_table(cls):
        table_sql = """
        DROP TABLE "{0}" CASCADE;
        """.format(cls.prep_table)
        execute_query(table_sql)
        
    @classmethod                
    def create_parent_table(cls, name):
        '''
        Create table that will be used for these tags,
        dynamically named.
        '''
        name = 'tag_%s' % name
        cls.set_table_name(name)
        table_sql = """
        CREATE TABLE "%s" (
            id integer NOT NULL,
            chromosome_id integer default NULL,
            strand smallint default NULL,
            "start" bigint,
            "end" bigint,
            start_end int8range,
            refseq boolean default false
        );
        CREATE SEQUENCE "%s_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "%s_id_seq" OWNED BY "%s".id;
        ALTER TABLE "%s" ALTER COLUMN id 
            SET DEFAULT nextval('"%s_id_seq"'::regclass);
        ALTER TABLE ONLY "%s" ADD CONSTRAINT %s_pkey PRIMARY KEY (id);
        """ % (cls._meta.db_table, 
               cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, cls.name)
        execute_query(table_sql)
        
        cls.table_created = True
    
    @classmethod
    def create_partition_tables(cls):
        '''
        Can't be multiprocessed; too many attempts to ANALYZE at once.
        '''
        
        for chr_id in current_settings.GENOME_CHOICES[current_settings.GENOME]['chromosomes']:
            table_sql = """
            CREATE TABLE "%s_%d" (
                CHECK ( chromosome_id = %d )
            ) INHERITS ("%s");""" % (cls._meta.db_table,
                                     chr_id, chr_id,
                                     cls._meta.db_table)
            execute_query(table_sql)
        
        trigger_sql = '''
            CREATE OR REPLACE FUNCTION %s.atlas_tag_insert_trigger()
            RETURNS TRIGGER AS $$
            DECLARE
                refseq_string text;
                start_end_string text;
            BEGIN
                IF NEW.refseq IS NULL THEN
                    refseq_string := 'NULL';
                ELSE
                    refseq_string := NEW.refseq::text;
                END IF;
                
                IF NEW.start_end IS NULL THEN
                    start_end_string := 'NULL';
                ELSE
                    start_end_string := 'int8range(' || quote_literal(NEW.start) || ',' 
                    || quote_literal(NEW."end") || ', ''[]'')';
                END IF;
                EXECUTE 'INSERT INTO "%s_' || NEW.chromosome_id || '" VALUES ('
                || quote_literal(NEW.id) || ','
                || quote_literal(NEW.chromosome_id) || ','
                || quote_literal(NEW.strand) || ','
                || quote_literal(NEW.start) || ','
                || quote_literal(NEW."end") || ','
                || start_end_string || ','
                || refseq_string || ')';
                RETURN NULL;
            END;
            $$
            LANGUAGE 'plpgsql';
            
            -- Trigger function for inserts on main table
            CREATE TRIGGER atlas_tag_trigger
                BEFORE INSERT ON "%s"
                FOR EACH ROW EXECUTE PROCEDURE %s.atlas_tag_insert_trigger();
        ''' % (current_settings.CURRENT_SCHEMA,
               cls._meta.db_table,
               cls._meta.db_table,
               current_settings.CURRENT_SCHEMA)
        execute_query(trigger_sql)
        
    @classmethod
    def translate_from_prep(cls):
        multiprocess_all_chromosomes(wrap_translate_from_prep, cls)
        
    @classmethod
    def _translate_from_prep(cls, chr_list):
        '''
        Take uploaded values and streamline into ints and sequence ends.
        '''
        for chr_id in chr_list:
            update_query = """
            INSERT INTO "{0}_{chr_id}" (chromosome_id, 
                                        strand, 
                                        "start", 
                                        "end", 
                                        start_end, 
                                        refseq)
            SELECT * FROM (
                SELECT {chr_id}, 
                (CASE WHEN prep.strand_char = '-' THEN 1 ELSE 0 END), 
                prep."start", 
                (prep."start" + char_length(prep.sequence_matched)),
                int8range(prep."start", 
                (prep."start" + char_length(prep.sequence_matched)), '[]'),
                NULL::boolean
            FROM "{1}" prep
            JOIN "{2}" chr ON chr.name = prep.chromosome
            WHERE chr.id = {chr_id}) derived;
            """.format(cls._meta.db_table, cls.prep_table,
                   Chromosome._meta.db_table,
                   chr_id=chr_id)
            execute_query(update_query)
                            
    @classmethod
    def set_refseq(cls):
        multiprocess_all_chromosomes(wrap_set_refseq, cls)
        
    @classmethod
    def _set_refseq(cls, chr_list):
        '''
        Set refseq status for segmentation during stitching later on by 
        overlapping with consolodated refseq transcripts.
        '''
        for chr_id in chr_list:
            print 'Setting Refseq status for chromosome {0}'.format(chr_id)
            update_query = """
            UPDATE "{0}_{1}" tag 
            SET refseq = NULL; 

            UPDATE "{0}_{1}" tag 
            SET refseq = true 
            FROM atlas_{2}_refseq_prep.atlas_transcript_{1} ref
            WHERE ref.start_end && tag.start_end
            AND ref.strand = tag.strand
            AND tag.refseq IS NULL;

            UPDATE "{0}_{1}" tag 
            SET refseq = false 
            WHERE refseq IS NULL;
            """.format(cls._meta.db_table, chr_id, current_settings.GENOME)
            execute_query(update_query)
            
    @classmethod
    def delete_prep_columns(cls):
        '''
        .. warning:: DELETES the associated sequence and strand_char columns to conserve space.
        
        '''
        table_sql = """ 
        ALTER TABLE "%s" DROP COLUMN sequence_matched;
        ALTER TABLE "%s" DROP COLUMN strand_char;
        ALTER TABLE "%s" DROP COLUMN chromosome;
        """ % (cls._meta.db_table, cls._meta.db_table, cls._meta.db_table)
        execute_query(table_sql)
        
        cls.table_created = False

    @classmethod
    def add_indices(cls):
        multiprocess_all_chromosomes(wrap_add_indices, cls)
        
    @classmethod
    def _add_indices(cls, chr_list):
        for chr_id in chr_list:
            update_query = """
            CREATE INDEX {0}_{chr_id}_pkey_idx ON "{1}_{chr_id}" USING btree (id);
            CREATE INDEX {0}_{chr_id}_chr_idx ON "{1}_{chr_id}" USING btree (chromosome_id);
            CREATE INDEX {0}_{chr_id}_strand_idx ON "{1}_{chr_id}" USING btree (strand);
            CREATE INDEX {0}_{chr_id}_start_end_idx ON "{1}_{chr_id}" USING gist (start_end);
            ANALYZE "{1}_{chr_id}";
            """.format(cls.name, cls._meta.db_table, chr_id=chr_id)
            execute_query(update_query)
            
    @classmethod 
    def add_record_of_tags(cls):
        '''
        Add SequencingRun record with the details of this run.
        
        Should be called only after all tags have been added.
        '''
        connection.close()
        # If possible, retrieve bowtie stats
        s, _ = SequencingRun.objects.get_or_create(source_table=cls._meta.db_table)
        return s