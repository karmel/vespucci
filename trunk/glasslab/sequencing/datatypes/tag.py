'''
Created on Sep 27, 2010

@author: karmel
'''
from __future__ import division
from django.db import models
from django.db import connection, transaction
from glasslab.utils.datatypes.genome_reference import SequenceTranscriptionRegion,\
    NonCodingTranscriptionRegion, PatternedTranscriptionRegion, SequenceExon,\
    ConservedTranscriptionRegion, Chromosome
from multiprocessing import Pool
import math

def multiprocess_glass_tags(func, cls):
    ''' 
    Convenience method for splitting up queries based on glass tag id.
    '''
    print GlassTag.chromosomes()
    total_count = len(GlassTag.chromosomes())
    p = Pool(8)
    step = int(math.ceil(total_count/8))
    for start in xrange(0,total_count,step):
        p.apply_async(func, args=(cls, GlassTag.chromosomes()[start:(start+step)]))
    p.close()
    p.join()

# The following methods wrap bound methods. This is necessary
# for use with multiprocessing. Note that getattr with dynamic function names
# doesn't seem to work either.
def wrap_translate_from_bowtie(cls, chr_list): cls._translate_from_bowtie(chr_list)
def wrap_set_start_end_cube(cls, chr_list): cls._set_start_end_cube(chr_list)
def wrap_insert_matching_tags(cls, chr_list): cls._insert_matching_tags(chr_list)
def wrap_update_start_site_tags(cls, chr_list): cls._update_start_site_tags(chr_list)
def wrap_update_exon_tags(cls, chr_list): cls._update_exon_tags(chr_list)
        
class DynamicTable(models.Model):
    name = None
    table_created = None
    
    class Meta: abstract = True
    
    @classmethod
    def set_table_name(cls, table_name):
        '''
        Set table name for class, incorporating into schema specification.
        '''
        cls._meta.db_table = 'current_projects"."%s' % table_name
        cls.name = table_name      
    
class GlassTag(DynamicTable):
    '''
    From bowtie::
    
        tag id                                    strand    chr    start            sequence_matched                       quality_score                            other_valid_alignments    mismatches
        51 HWUSI-EAS291_0001:4:1:1045:14123#0/1    -       chr5    66529332        ATTAGTTGACAGGAATTAGCTAGGAACCACAGAA      bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb      0       0:C>A

    Streamlined output::
        
        strand    chr    start            sequence_matched
        -       chr5    66529332        ATTAGTTGACAGGAATTAGCTAGGAACCACAGAA

    
    '''
    strand                  = models.IntegerField(max_length=1)
    chromosome              = models.ForeignKey(Chromosome)
    start                   = models.IntegerField(max_length=12)
    end                     = models.IntegerField(max_length=12)
    
    @classmethod        
    def create_table(cls, name):
        '''
        Create table that will be used for these tags,
        dynamically named.
        '''
        if cls.table_created: print 'Warning: Glass Tag table has already been created.'
        name = 'tag_%s' % name
        cls.set_table_name(name)
        table_sql = """
        CREATE TABLE "%s" (
            id integer NOT NULL,
            chromosome_id integer default NULL,
            strand smallint default NULL,
            strand_char character(1) default NULL,
            chromosome character(20),
            "start" bigint,
            "end" bigint,
            start_end public.cube,
            sequence_matched character(100)
        );
        CREATE SEQUENCE "%s_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "%s_id_seq" OWNED BY "%s".id;
        ALTER TABLE "%s" ALTER COLUMN id SET DEFAULT nextval('"%s_id_seq"'::regclass);
        ALTER TABLE ONLY "%s" ADD CONSTRAINT %s_pkey PRIMARY KEY (id);
        """ % (cls._meta.db_table, 
               cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, name)
        cursor = connection.cursor()
        cursor.execute(table_sql)
        transaction.commit_unless_managed()
        
        cls.table_created = True
    
    _chromosomes = None
    @classmethod 
    def chromosomes(cls): 
        if not cls._chromosomes:
            cls._chromosomes = cls.objects.values('chromosome').distinct().values_list('chromosome_id',flat=True)
        return cls._chromosomes
           
    @classmethod
    def associate_chromosome(cls):
        '''
        Take bowtied uploaded values and streamline into ints and sequence ends.
        '''
        update_query = """
        UPDATE "%s" tag SET chromosome_id = chr.id
        FROM "%s" chr WHERE tag.chromosome = chr.name;
        """ % (cls._meta.db_table, Chromosome._meta.db_table,)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(update_query)
        transaction.commit_unless_managed()
    
    @classmethod
    def translate_from_bowtie(cls):
        multiprocess_glass_tags(wrap_translate_from_bowtie, cls)
        
    @classmethod
    def _translate_from_bowtie(cls, chr_list):
        '''
        Take bowtied uploaded values and streamline into ints and sequence ends.
        '''
        for chr_id in chr_list:
            update_query = """
            UPDATE "%s" SET strand = (CASE WHEN strand_char = '-' THEN 1 ELSE 0 END) WHERE chromosome_id = %d;
            UPDATE "%s" SET "end" = ("start" + char_length(sequence_matched)) WHERE chromosome_id = %d;
            """ % (cls._meta.db_table,cls._meta.db_table,
                   chr_id,
                   chr_id)
            connection.close()
            cursor = connection.cursor()
            cursor.execute(update_query)
            transaction.commit_unless_managed()
             
    @classmethod
    def set_start_end_cube(cls):
        multiprocess_glass_tags(wrap_set_start_end_cube, cls)
        
    @classmethod
    def _set_start_end_cube(cls, chr_list):
        '''
        Create type cube field for faster interval searching with the PostgreSQL cube package.
        '''
        for chr_id in chr_list:
            update_query = """
            UPDATE "%s" set start_end = public.cube("start"::float,"end"::float) WHERE chromosome_id = %d;
            """ % (cls._meta.db_table, chr_id)
            connection.close()
            cursor = connection.cursor()
            cursor.execute(update_query)
            transaction.commit_unless_managed()
            
    @classmethod
    def delete_bowtie_columns(cls):
        '''
        .. warning:: DELETES the associated sequence and strand_char columns to conserve space.
        
        '''
        table_sql = """ 
        ALTER TABLE "%s" DROP COLUMN sequence_matched;
        ALTER TABLE "%s" DROP COLUMN strand_char;
        ALTER TABLE "%s" DROP COLUMN chromosome;
        """ % (cls._meta.db_table, cls._meta.db_table, cls._meta.db_table)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(table_sql)
        transaction.commit_unless_managed()
        
        cls.table_created = False

    @classmethod
    def add_chromosome_index(cls):
        update_sql = """
        CREATE INDEX %s_chr_idx ON "%s" USING btree (chromosome_id);
        CREATE INDEX %s_start_end_idx ON "%s" USING gist (chromosome_id);
        """ % (cls.name, cls._meta.db_table,
               cls.name, cls._meta.db_table)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(update_sql)
        transaction.commit_unless_managed()
                          

class GlassTagTranscriptionRegionTable(DynamicTable):
    glass_tag       = models.ForeignKey(GlassTag)
    
    table_type      = None
    
    class Meta: abstract = True
    
    @classmethod        
    def create_table(cls, name):
        '''
        Create table that will be used for these tags,
        dynamically named.
        '''
        if cls.table_created: print 'Warning: Glass Tag to %s Transcription table has already been created.' % cls.table_type
        name = 'tag_%s_%s' % (cls.table_type,name)
        cls.set_table_name(name)
        table_sql = """
        CREATE TABLE "%s" (
            id integer NOT NULL,
            glass_tag_id integer REFERENCES "%s",
            %s_transcription_region_id integer REFERENCES "%s"
        );
        CREATE SEQUENCE "%s_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "%s_id_seq" OWNED BY "%s".id;
        ALTER TABLE "%s" ALTER COLUMN id SET DEFAULT nextval('"%s_id_seq"'::regclass);
        ALTER TABLE ONLY "%s" ADD CONSTRAINT %s_pkey PRIMARY KEY (id);
        """ % (cls._meta.db_table,
               GlassTag._meta.db_table,
               cls.related_class._meta.db_table, 
               cls.table_type,
               cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, name)
        cursor = connection.cursor()
        cursor.execute(table_sql)
        transaction.commit_unless_managed()
        
        cls.table_created = True
    
    @classmethod
    def insert_matching_tags(cls):
        multiprocess_glass_tags(wrap_insert_matching_tags, cls)
        
    @classmethod
    def _insert_matching_tags(cls, chr_list):
        '''
        Insert records where either the start or the end of the tag 
        are within the boundaries of the sequence region.
        '''
        for chr_id in chr_list:
            insert_sql = """
            INSERT INTO
                "%s" (glass_tag_id, sequence_transcription_region_id)
            SELECT * FROM
                (SELECT tag.id, reg.id
                FROM "%s" tag
                JOIN "%s" reg
                ON tag.start_end OPERATOR(public.&&) reg.start_end
                WHERE tag.chromosome_id = %d AND reg.chromosome_id = %d) derived;
            """ % (cls._meta.db_table, 
                   GlassTag._meta.db_table,
                   cls.related_class._meta.db_table,
                   chr_id, chr_id)
            print insert_sql
            connection.close()
            cursor = connection.cursor()
            cursor.execute(insert_sql)
            transaction.commit_unless_managed()
        
    @classmethod  
    def add_indices(cls):
        update_sql = """
        CREATE INDEX %s_%s_idx ON "%s" USING btree (%s_transcription_region_id);
        """ % (cls.name,cls.table_type, 
               cls._meta.db_table, cls.table_type)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(update_sql)
        transaction.commit_unless_managed() 
    
class GlassTagSequence(GlassTagTranscriptionRegionTable):
    '''
    Relationship between GlassTag and the sequence record it maps to.
    '''
    sequence_transcription_region   = models.ForeignKey(SequenceTranscriptionRegion)
    exon                            = models.BooleanField(default=False)
    start_site                      = models.BooleanField(default=False)
    
    table_type = 'sequence'
    related_class = SequenceTranscriptionRegion
    
    @classmethod        
    def create_table(cls, name):
        '''
        Create table that will be used for these tags,
        dynamically named.
        '''
        if cls.table_created: print 'Warning: Glass Tag to Sequence Transcription table has already been created.'
        name = 'tag_sequence_%s' % name
        cls.set_table_name(name)
        
        table_sql = """
        CREATE TABLE "%s" (
            id integer NOT NULL,
            glass_tag_id integer REFERENCES "%s",
            sequence_transcription_region_id integer REFERENCES "%s",
            exon smallint default 0,
            start_site smallint default 0
        );
        CREATE SEQUENCE "%s_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "%s_id_seq" OWNED BY "%s".id;
        ALTER TABLE "%s" ALTER COLUMN id SET DEFAULT nextval('"%s_id_seq"'::regclass);
        ALTER TABLE ONLY "%s" ADD CONSTRAINT %s_pkey PRIMARY KEY (id);
        """ % (cls._meta.db_table,
               GlassTag._meta.db_table,
               cls.related_class._meta.db_table, 
               cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, name)
        cursor = connection.cursor()
        cursor.execute(table_sql)
        transaction.commit_unless_managed()
        
        cls.table_created = True
    
    promotion_cutoff = 1000
    
    @classmethod  
    def update_start_site_tags(cls):
        '''
        If the start of a tag is within 1kb of the 
        start (if + strand) or the start of a tag is within
        1kb of the end (if - strand) of the region,
        mark as a start_site.
        '''
        update_sql = """
        UPDATE "%s" tag_seq
        SET start_site = 1
        FROM "%s" tag, "%s" reg
        WHERE 
        tag_seq.sequence_transcription_region_id = reg.id
        AND tag_seq.glass_tag_id = tag.id
        AND tag.start_end OPERATOR(public.&&) reg.start_site;
        """ % (cls._meta.db_table, 
               GlassTag._meta.db_table,
               SequenceTranscriptionRegion._meta.db_table)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(update_sql)
        transaction.commit_unless_managed()
        
    @classmethod  
    def update_exon_tags(cls):
        multiprocess_glass_tags(wrap_update_exon_tags, cls)

    @classmethod  
    def _update_exon_tags(cls, chr_list):
        '''
        If a tag is within the exon of the sequence associated,
        set exon = 1
        '''
        for chr_id in chr_list:
            update_sql = """
            UPDATE
                "%s" tag_seq
            SET exon = 1
            FROM "%s" tag, "%s" ex
            WHERE
                tag_seq.sequence_transcription_region_id = ex.sequence_transcription_region_id
                AND tag.chromosome_id = %d
                AND tag_seq.glass_tag_id = tag.id
                AND ((tag."start" >= ex.exon_start
                        AND tag."start" <= ex.exon_end)
                    OR (tag."end" >= ex.exon_start
                        AND tag."end" <= ex.exon_end));
            """ % (cls._meta.db_table, 
                   GlassTag._meta.db_table,
                   SequenceExon._meta.db_table,
                   chr_id)
            connection.close()
            cursor = connection.cursor()
            cursor.execute(update_sql)
            transaction.commit_unless_managed()
        
class GlassTagNonCoding(GlassTagTranscriptionRegionTable):
    '''
    Relationship between GlassTag and the non coding region it maps to.
    '''
    non_coding_transcription_region = models.ForeignKey(NonCodingTranscriptionRegion)
    
    table_type = 'non_coding'
    related_class = NonCodingTranscriptionRegion
    
class GlassTagPatterned(GlassTagTranscriptionRegionTable):
    '''
    Relationship between GlassTag and the patterned region it maps to.
    '''
    patterned_transcription_region  = models.ForeignKey(PatternedTranscriptionRegion)
    
    table_type = 'patterned'
    related_class = PatternedTranscriptionRegion
    
class GlassTagConserved(GlassTagTranscriptionRegionTable):
    '''
    Relationship between GlassTag and the conservation region it maps to.
    '''
    conserved_transcription_region  = models.ForeignKey(ConservedTranscriptionRegion)
    
    table_type = 'conserved'
    related_class = ConservedTranscriptionRegion
    