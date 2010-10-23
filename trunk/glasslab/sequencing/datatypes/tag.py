'''
Created on Sep 27, 2010

@author: karmel
'''
from django.db import models
from django.db import connection, transaction
from glasslab.utils.datatypes.genome_reference import SequenceTranscriptionRegion,\
    NonCodingTranscriptionRegion, PatternedTranscriptionRegion, SequenceExon,\
    ConservedTranscriptionRegion, Chromosome
from multiprocessing import Pool
import math

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
    
    @classmethod
    def translate_from_bowtie(cls):
        '''
        Take bowtied uploaded values and streamline into ints and sequence ends.
        '''
        update_query = """
        UPDATE "%s" SET strand = (CASE WHEN strand_char = '-' THEN 1 ELSE 0 END);
        UPDATE "%s" SET "end" = ("start" + char_length(sequence_matched));
        """ % (cls._meta.db_table,cls._meta.db_table)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(update_query)
        transaction.commit_unless_managed()
            
    @classmethod
    def associate_chromosome(cls):
        '''
        Take bowtied uploaded values and streamline into ints and sequence ends.
        '''
        update_query = """
        UPDATE "%s" tag SET chromosome_id = chr.id
        FROM "%s" chr WHERE tag.chromosome = chr.name;
        """ % (cls._meta.db_table, Chromosome._meta.db_table)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(update_query)
        transaction.commit_unless_managed()
            
    @classmethod
    def set_start_end_cube(cls):
        '''
        Create type cube field for faster interval searching with the PostgreSQL cube package.
        '''
        update_query = """
        UPDATE "%s" set start_end = public.cube("start"::float,"end"::float);
        """ % cls._meta.db_table
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
    def set_bins(cls):
        '''
        Set bins according to bitwise operation algorithm used by UCSC, SAM, etc:
        
            In the following, each bin may span 2^29, 2^26, 2^23, 2^20, 2^17 or 2^14 bp. 
            Bin 0 spans a 512Mbp region, bins 1-8 span 64Mbp, 
            9-72 8Mbp, 73-584 1Mbp, 585-4680 128Kbp and bins 4681-37449 span 16Kbp regions. 
            
        (From http://samtools.sourceforge.net/SAM1.pdf)
        '''
        sets = ((14,15),(17,12),(20,9),(23,6),(26,3))
        for span, shift in sets:
            # Not that these all block each other; no gain in multiprocessing.
            cls._set_bin(span, shift)
        
    @classmethod
    def _set_bin(cls, span, shift):
            update_sql = """
            UPDATE "%s"
            SET 
                full_bin = (chromosome_id * 100000 + (((1<<%d)-1)/7 + ("start">>%d))), 
                bin = (((1<<%d)-1)/7 + ("start">>%d))
            WHERE 
                    ("start">>%d = "end">>%d);
            """ % (cls._meta.db_table,
                   shift, span, 
                   shift, span, 
                   span, span)
            connection.close()
            cursor = connection.cursor()
            cursor.execute(update_sql)
            transaction.commit_unless_managed()

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
            glass_tag_id integer,
            %s_transcription_region_id integer
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
        """ % (cls._meta.db_table, cls.table_type,
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
        '''
        Multi-process and split by id to conserve time.
        '''
        total_count = cls.objects.count()
        p = Pool(8)
        step = int(math.ceil(total_count/8))
        for start in xrange(0,total_count,step):
            p.apply_async(wrap_insert_matching_tags, args=(cls, start, start + step))
        p.close()
        p.join()
        
    @classmethod
    def _insert_matching_tags(cls, start, stop):
        '''
        Insert records where either the start or the end of the tag 
        are within the boundaries of the sequence region.
        '''
        insert_sql = """
        INSERT INTO
            "%s" (glass_tag_id, sequence_transcription_region_id)
        SELECT * FROM
            (SELECT tag.id, reg.id
            FROM "%s" tag
            JOIN "%s" reg
            ON
                tag.chromosome_id = reg.chromosome_id
                AND tag.start_end OPERATOR(public.&&) reg.start_end
            WHERE tag.id > %d AND tag.id <= %d) derived;
        """ % (cls._meta.db_table, 
               GlassTag._meta.db_table,
               cls.related_class._meta.db_table,
               start, stop)
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

def wrap_insert_matching_tags(cls, start, stop):
    '''
    For use with multiprocessing
    '''
    cls._insert_matching_tags(start, stop)
    
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
            glass_tag_id integer,
            sequence_transcription_region_id integer,
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
        AND ((reg.strand = 0
            AND tag.start <= (reg.transcription_start + %d))
            OR (reg.strand = 1
            AND tag.end >= (reg.transcription_end - %d)));
        """ % (cls._meta.db_table, 
               GlassTag._meta.db_table,
               SequenceTranscriptionRegion._meta.db_table,
               cls.promotion_cutoff, cls.promotion_cutoff)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(update_sql)
        transaction.commit_unless_managed()
        
    @classmethod  
    def update_exon_tags(cls):
        '''
        If a tag is within the exon of the sequence associated,
        set exon = 1
        '''
        update_sql = """
        UPDATE
            "%s" tag_seq
        SET exon = 1
        FROM "%s" tag, "%s" ex
        WHERE
            tag_seq.sequence_transcription_region_id = ex.sequence_transcription_region_id
            AND tag_seq.glass_tag_id = tag.id
            AND ((tag."start" >= ex.exon_start
                    AND tag."start" <= ex.exon_end)
                OR (tag."end" >= ex.exon_start
                    AND tag."end" <= ex.exon_end));
        """ % (cls._meta.db_table, 
               GlassTag._meta.db_table,
               SequenceExon._meta.db_table)
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
    