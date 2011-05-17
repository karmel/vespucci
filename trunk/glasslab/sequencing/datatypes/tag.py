'''
Created on Sep 27, 2010

@author: karmel
'''
from __future__ import division
from django.db import models, utils, connection
from glasslab.utils.datatypes.genome_reference import SequenceTranscriptionRegion,\
    NonCodingTranscriptionRegion, PatternedTranscriptionRegion, SequenceExon,\
    ConservedTranscriptionRegion, Chromosome
from multiprocessing import Pool
import traceback
from glasslab.config import current_settings
from glasslab.utils.datatypes.basic_model import DynamicTable, BoxField
from glasslab.glassatlas.datatypes.metadata import SequencingRun
from glasslab.utils.database import execute_query, fetch_rows
from datetime import datetime
import os
import re

def multiprocess_glass_tags(func, cls, *args):
    ''' 
    Convenience method for splitting up queries based on glass tag id.
    '''
    total_count = len(GlassTag.chromosomes())
    processes = current_settings.ALLOWED_PROCESSES
    p = Pool(processes)
    # Chromosomes are sorted by count descending, so we want to interleave them
    # in order to create even-ish groups.
    chr_lists = [[GlassTag.chromosomes()[x] for x in xrange(i,total_count,processes)] 
                                for i in xrange(0,processes)]
    
    for chr_list in chr_lists:
        p.apply_async(func, args=[cls, chr_list,] + list(args))
    p.close()
    p.join()

# The following methods wrap bound methods. This is necessary
# for use with multiprocessing. Note that getattr with dynamic function names
# doesn't seem to work either.
def wrap_errors(func, *args):
    try: func(*args)
    except Exception:
        print 'Encountered exception in wrapped function:\n%s' % traceback.format_exc()
        raise
    
def wrap_partition_tables(cls, chr_list): wrap_errors(cls._create_partition_tables, chr_list)
def wrap_translate_from_bowtie(cls, chr_list): wrap_errors(cls._translate_from_bowtie, chr_list)
def wrap_delete_tags(cls, chr_list): wrap_errors(cls._delete_tags, chr_list)
def wrap_set_start_end_box(cls, chr_list): wrap_errors(cls._set_start_end_box, chr_list)
def wrap_set_polya(cls, chr_list): wrap_errors(cls._set_polya, chr_list)
def wrap_insert_matching_tags(cls, chr_list): wrap_errors(cls._insert_matching_tags, chr_list)
def wrap_update_start_site_tags(cls, chr_list): wrap_errors(cls._update_start_site_tags, chr_list)
def wrap_update_exon_tags(cls, chr_list): wrap_errors(cls._update_exon_tags, chr_list)
def wrap_add_indices(cls, chr_list): wrap_errors(cls._add_indices, chr_list)
    
def set_all_tag_table_names(base_table_name):
    '''
    Convenience method for setting all Dynamic tag table names.
    '''
    GlassTag.set_table_name('tag_%s' % base_table_name)
    GlassTagSequence.set_table_name('tag_sequence_%s' % base_table_name)
    GlassTagNonCoding.set_table_name('tag_non_coding_%s' % base_table_name)
    GlassTagConserved.set_table_name('tag_conserved_%s' % base_table_name)
    GlassTagPatterned.set_table_name('tag_patterned_%s' % base_table_name)

class GlassSequencingOutput(DynamicTable):
    '''
    Parent class for tags and peaks.
    '''
    _chromosomes = None
    @classmethod 
    def chromosomes(cls): 
        return list(xrange(1,23))
        if not cls._chromosomes:
            if cls._meta.db_table:
                chr_sql = """
                    SELECT chromosome_id FROM "%s" tag
                    GROUP BY chromosome_id
                    ORDER BY count(chromosome_id) DESC;
                    """ % (cls._meta.db_table)
                rows = fetch_rows(chr_sql)
                if rows:
                    cls._chromosomes = zip(*rows)[0]
            
            if not cls._chromosomes and cls.bowtie_table:
                # Tag table doesn't exist yet
                chr_sql = """
                SELECT chr.id FROM "%s" chr
                JOIN (
                    SELECT chromosome, count(chromosome) 
                    FROM "%s" 
                    GROUP BY chromosome
                ) derived
                ON chr.name = derived.chromosome
                ORDER BY derived.count DESC;
                """ % (Chromosome._meta.db_table, cls.bowtie_table)
                rows = fetch_rows(chr_sql)
                cls._chromosomes = zip(*rows)[0]
            elif not cls._chromosomes:
                chr_sql = """
                SELECT id FROM "%s";
                """ % (Chromosome._meta.db_table)
                rows = fetch_rows(chr_sql)
                cls._chromosomes = zip(*rows)[0]
            
        return cls._chromosomes
    
    class Meta: abstract = True
    
class GlassTag(GlassSequencingOutput):
    '''
    From bowtie::
    
        tag id                                    strand    chr    start            sequence_matched                       quality_score                            other_valid_alignments    mismatches
        51 HWUSI-EAS291_0001:4:1:1045:14123#0/1    -       chr5    66529332        ATTAGTTGACAGGAATTAGCTAGGAACCACAGAA      bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb      0       0:C>A

    Streamlined output::
        
        strand    chr    start            sequence_matched
        -       chr5    66529332        ATTAGTTGACAGGAATTAGCTAGGAACCACAGAA

    
    '''
    bowtie_table = None

    chromosome              = models.ForeignKey(Chromosome)
    strand                  = models.IntegerField(max_length=1)
    start                   = models.IntegerField(max_length=12)
    end                     = models.IntegerField(max_length=12)
    
    start_end               = BoxField(max_length=255, help_text='This is a placeholder for the PostgreSQL box type.', null=True)
    
    polya                   = models.NullBooleanField(default=None)
    
    @classmethod        
    def create_bowtie_table(cls, name):
        '''
        Create table that will be used for to upload bowtied information,
        dynamically named.
        '''
        cls.set_bowtie_table('bowtie_%s' % name)
        table_sql = """
        CREATE TABLE "%s" (
            strand_char character(1) default NULL,
            chromosome character(20),
            "start" bigint,
            sequence_matched character(100)
        );
        """ % cls.bowtie_table
        execute_query(table_sql)
    
    @classmethod 
    def set_bowtie_table(cls, name): 
        cls.bowtie_table = '%s"."%s' % (current_settings.CURRENT_SCHEMA, name)

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
            start_end box,
            polya boolean default false
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
               cls._meta.db_table, cls.name)
        execute_query(table_sql)
        
        cls.table_created = True
    
    @classmethod
    def create_partition_tables(cls):
        '''
        Can't be multiprocessed; too many attempts to ANALYZE at once.
        '''
        
        for chr_id in cls.chromosomes():
            table_sql = """
            CREATE TABLE "%s_%d" (
                CHECK ( chromosome_id = %d )
            ) INHERITS ("%s");""" % (cls._meta.db_table,
                                     chr_id, chr_id,
                                     cls._meta.db_table)
            execute_query(table_sql)
        
        trigger_sql = '''
            CREATE OR REPLACE FUNCTION %s.glass_tag_insert_trigger()
            RETURNS TRIGGER AS $$
            DECLARE
                polya_string text;
                start_end_string text;
            BEGIN
                IF NEW.polya IS NULL THEN
                    polya_string := 'NULL';
                ELSE
                    polya_string := NEW.polya::text;
                END IF;
                
                IF NEW.start_end IS NULL THEN
                    start_end_string := 'NULL';
                ELSE
                    start_end_string := 'public.make_box(' || quote_literal(NEW.start) || ', 0, ' 
                    || quote_literal(NEW."end") || ', 0)';
                END IF;
                EXECUTE 'INSERT INTO "%s_' || NEW.chromosome_id || '" VALUES ('
                || quote_literal(NEW.id) || ','
                || quote_literal(NEW.chromosome_id) || ','
                || quote_literal(NEW.strand) || ','
                || quote_literal(NEW.start) || ','
                || quote_literal(NEW."end") || ','
                || start_end_string || ','
                || polya_string || ')';
                RETURN NULL;
            END;
            $$
            LANGUAGE 'plpgsql';
            
            -- Trigger function for inserts on main table
            CREATE TRIGGER glass_tag_trigger
                BEFORE INSERT ON "%s"
                FOR EACH ROW EXECUTE PROCEDURE %s.glass_tag_insert_trigger();
        ''' % (current_settings.CURRENT_SCHEMA,
               cls._meta.db_table,
               cls._meta.db_table,
               current_settings.CURRENT_SCHEMA)
        execute_query(trigger_sql)
        
    @classmethod
    def associate_chromosome(cls):
        '''
        Take bowtied uploaded values and streamline into ints and sequence ends.
        '''
        update_query = """
        UPDATE "%s" tag SET chromosome_id = chr.id
        FROM "%s" chr WHERE tag.chromosome = chr.name;
        """ % (cls._meta.db_table, Chromosome._meta.db_table,)
        execute_query(update_query)
    
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
            INSERT INTO "%s_%d" (chromosome_id, strand, "start", "end", start_end, polya)
            SELECT * FROM (
                SELECT %d, (CASE WHEN bowtie.strand_char = '-' THEN 1 ELSE 0 END), 
                bowtie."start", (bowtie."start" + char_length(bowtie.sequence_matched)),
                public.make_box(bowtie."start", 0, (bowtie."start" + char_length(bowtie.sequence_matched)), 0),
                NULL::boolean
            FROM "%s" bowtie
            JOIN "%s" chr ON chr.name = bowtie.chromosome
            WHERE chr.id = %d) derived;
            """ % (cls._meta.db_table,chr_id,
                   chr_id, cls.bowtie_table,
                   Chromosome._meta.db_table,
                   chr_id)
            execute_query(update_query)
    @classmethod
    def delete_tags(cls):
        multiprocess_glass_tags(wrap_delete_tags, cls)
        
    @classmethod
    def _delete_tags(cls, chr_list):
        '''
        Take bowtied uploaded values and streamline into ints and sequence ends.
        '''
        for chr_id in chr_list:
            update_query = """
            DELETE FROM "%s" bowtie
            WHERE chromosome = (SELECT name FROM "%s"
                WHERE id = %d)
            AND start IN (SELECT start FROM "%s_%d" tag
                WHERE strand = 0)
            AND strand_char = '+';
            DELETE FROM "%s" bowtie
            WHERE chromosome = (SELECT name FROM "%s"
                WHERE id = %d)
            AND start IN (SELECT start FROM "%s_%d" tag
                WHERE strand = 1)
            AND strand_char = '-';
            DELETE FROM "%s_%d" tag
            WHERE start_end IS NULL;
            """ % (cls.bowtie_table,
                   Chromosome._meta.db_table, chr_id,
                   cls._meta.db_table,chr_id,
                   cls.bowtie_table,
                   Chromosome._meta.db_table, chr_id,
                   cls._meta.db_table,chr_id,
                   cls._meta.db_table,chr_id,
                   )
            
            execute_query(update_query)
                    
    @classmethod
    def set_start_end_box(cls):
        multiprocess_glass_tags(wrap_set_start_end_box, cls)
        
    @classmethod
    def _set_start_end_box(cls, chr_list):
        '''
        Create type box field for faster interval searching with the PostgreSQL box.
        '''
        for chr_id in chr_list:
            update_query = """
            UPDATE "%s" set start_end = public.make_box("start", 0, "end", 0) WHERE chromosome_id = %d;
            """ % (cls._meta.db_table, chr_id)
            execute_query(update_query)
    
    @classmethod
    def set_polya(cls):
        multiprocess_glass_tags(wrap_set_polya, cls)
        
    @classmethod
    def _set_polya(cls, chr_list):
        '''
        Create type box field for faster interval searching with the PostgreSQL box.
        '''
        for chr_id in chr_list:
            update_query = """
            -- IGNORE strand, since either side match is a match
            UPDATE "%s_%d" tag 
            SET polya = true 
            FROM genome_reference_mm9.tag_polya_region_%d pol
            WHERE tag.start_end @> pol.start_end
            AND polya IS NULL;

            UPDATE "%s_%d" tag 
            SET polya = false 
            WHERE polya IS NULL;
            """ % (cls._meta.db_table, chr_id, chr_id,
                   cls._meta.db_table, chr_id)
            execute_query(update_query)
            
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
        execute_query(table_sql)
        
        cls.table_created = False

    @classmethod
    def add_indices(cls):
        multiprocess_glass_tags(wrap_add_indices, cls)
        
    @classmethod
    def _add_indices(cls, chr_list):
        for chr_id in chr_list:
            update_query = """
            CREATE INDEX %s_%d_chr_idx ON "%s_%d" USING btree (chromosome_id);
            CREATE INDEX %s_%d_strand_idx ON "%s_%d" USING btree (strand);
            CREATE INDEX %s_%d_start_end_idx ON "%s_%d" USING gist (start_end);
            ANALYZE "%s_%d";
            """ % (cls.name, chr_id, cls._meta.db_table, chr_id,
                   cls.name, chr_id, cls._meta.db_table, chr_id,
                   cls.name, chr_id, cls._meta.db_table, chr_id,
                   cls._meta.db_table, chr_id)
            execute_query(update_query)
    
    @classmethod 
    def add_record_of_tags(cls, description='', type='Gro-Seq', standard=False, stats_file=None):
        '''
        Add SequencingRun record with the details of this run.
        
        Should be called only after all tags have been added.
        '''
        connection.close()
        # If possible, retrieve bowtie stats
        try:
            f = file(stats_file)
            for i,line in enumerate(f.readlines()):
                if i > 4: raise Exception # Something is wrong with this file
                if line.find('reads with at least one reported alignment') >= 0:
                    pieces = line.split()
                    percent_mapped = float(re.search('([\d\.]+)',pieces[-1:][0]).group(0))
                    break
        except: 
            percent_mapped = None
            
        s, created = SequencingRun.objects.get_or_create(source_table=cls._meta.db_table,
                                        defaults={'name': cls.name, 
                                                  'total_tags': cls.objects.count(),
                                                  'description': description,
                                                  'cell_type': current_settings.CURRENT_CELL_TYPE,
                                                  'type': type,
                                                  'standard': standard,
                                                  'percent_mapped': percent_mapped }
                                               )
        if not created: 
            s.total_tags = cls.objects.count()
            s.percent_mapped = percent_mapped
            s.save() 
        return s

    @classmethod
    def fix_tags(cls, bowtie_row):
        '''
        Method implemented to fix existing tags without reloading all.
        '''
        chr = Chromosome.objects.get(name=bowtie_row[1])
        tags = cls.objects.filter(chromosome=chr,
                                  start=int(bowtie_row[2]),
                                  start_end=None).order_by('id')
        
        if not tags: 
            tag = cls(chromosome=chr, start=int(bowtie_row[2]))
        else:
            tag = tags[0]

        tag.end = int(bowtie_row[2]) + len(bowtie_row[3])
        tag.start_end = (tag.start, 0, tag.end, 0)
        tag.strand = bowtie_row[0] == '-' and 1 or 0
        tag.save()
        connection.close()
        
    @classmethod
    def generate_bed_file(cls, output_dir):
        '''
        Generates a BED file (http://genome.ucsc.edu/FAQ/FAQformat.html#format1)
        of all the tags and their exons for viewing in the UCSC Genome Browser.
        '''
        
        transcripts = cls.objects.order_by('chromosome__id','start')
        cls._generate_bed_file(output_dir, transcripts, strand=0)
        cls._generate_bed_file(output_dir,transcripts, strand=1)
        
    @classmethod
    def _generate_bed_file(cls, output_dir, transcripts, strand=0):
        file_name = 'Glass_Transcripts_%s_%d.bed' % (datetime.now().strftime('%Y_%m_%d'), strand)
        file_path = os.path.join(output_dir, file_name)
        
        transcripts = transcripts.filter(strand=strand)
        
        strand_char = strand and '-' or '+'
        output = 'track name=%s_%d description="Glass Atlas %s Tags %s strand" useScore=1 itemRgb=On\n' \
                        % (cls.name, strand, cls.name, strand_char)
        
        for trans in transcripts:
            # chrom start end name score strand thick_start thick_end colors? exon_count csv_exon_sizes csv_exon_starts
            start = max(0,trans.start)
            end = min(trans.chromosome.length - 1,trans.end)
            row = [trans.chromosome.name, str(start), str(end), 
                   'Tag_' + str(trans.id),
                   trans.strand and '-' or '+', str(start), str(end), 
                   trans.strand and '0,255,0' or '0,0,255']
            output += '\t'.join(row) + '\n'
        
        f = open(file_path, 'w')
        f.write(output)
        f.close()
        
class GlassTagTranscriptionRegionTable(DynamicTable):
    glass_tag       = models.ForeignKey(GlassTag)
    
    table_type      = None
    related_class   = None
    partitioned     = False
    
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
        """ % (cls._meta.db_table,
               cls.table_type,
               cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, name)
        execute_query(table_sql)
        
        cls.table_created = True
    
    @classmethod
    def insert_matching_tags(cls):
        multiprocess_glass_tags(wrap_insert_matching_tags, cls)
    
    @classmethod 
    def _insert_matching_tags(cls, chr_list):
        if cls.partitioned: return cls._insert_matching_tags_by_chromosome(chr_list)
        else: return cls._insert_matching_tags_all(chr_list)
        
    @classmethod
    def _insert_matching_tags_all(cls, chr_list):
        '''
        Insert records where either the start or the end of the tag 
        are within the boundaries of the sequence region.
        '''
        for chr_id in chr_list:
            insert_sql = """
            INSERT INTO
                "%s" (glass_tag_id, %s_transcription_region_id)
            SELECT tag.id, reg.id
            FROM "%s_%d" tag, "%s" reg
            WHERE reg.chromosome_id = %d
                AND tag.start_end && reg.start_end;
            """ % (cls._meta.db_table, cls.table_type,
                   GlassTag._meta.db_table, chr_id,
                   cls.related_class._meta.db_table,
                   chr_id)
            execute_query(insert_sql)
              
    @classmethod
    def _insert_matching_tags_by_chromosome(cls, chr_list):
        '''
        Used for partitioned region tables.
        '''
        for chr_id in chr_list:
            try:
                insert_sql = """
                INSERT INTO
                    "%s" (glass_tag_id, %s_transcription_region_id)
                SELECT tag.id, reg.id
                FROM "%s_%d" tag, "%s_%d" reg
                WHERE reg.chromosome_id = %d
                    AND tag.start_end && reg.start_end;
                """ % (cls._meta.db_table, cls.table_type,
                       GlassTag._meta.db_table, chr_id,
                       cls.related_class._meta.db_table, chr_id,
                       chr_id)
                execute_query(insert_sql)
            except utils.DatabaseError:
                # Corresponding region_chr_id table doesn't exist.
                print 'Could not add %s region assignments for chromosome with id %d' % (cls.table_type, chr_id)
    
    @classmethod
    def add_indices(cls):
        update_sql = """
        CREATE INDEX %s_region_idx ON "%s" USING btree (%s_transcription_region_id);
        ANALYZE "%s";
        """ % (cls.table_type, cls._meta.db_table, cls.table_type,
               cls._meta.db_table)
        execute_query(update_sql)
    
class GlassTagSequence(GlassTagTranscriptionRegionTable):
    '''
    Relationship between GlassTag and the sequence record it maps to.
    '''
    sequence_transcription_region   = models.ForeignKey(SequenceTranscriptionRegion)
    exon                            = models.BooleanField(default=False)
    start_site                      = models.BooleanField(default=False)
    
    table_type = 'sequence'
    related_class = SequenceTranscriptionRegion
    partitioned     = False
    
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
            start_site_200 smallint default 0,
            start_site_1000 smallint default 0
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
        execute_query(table_sql)
        
        cls.table_created = True
    
    @classmethod
    def add_indices(cls):
        update_sql = """
        CREATE INDEX %s_region_idx ON "%s" USING btree (%s_transcription_region_id);
        CREATE INDEX %s_glass_tag_idx ON "%s" USING btree (glass_tag_id);
        ANALYZE "%s";
        """ % (cls.name, cls._meta.db_table, cls.table_type,
               cls.name, cls._meta.db_table,
               cls._meta.db_table)
        execute_query(update_sql)
          
    @classmethod  
    def update_start_site_tags(cls):
        multiprocess_glass_tags(wrap_update_start_site_tags, cls)
        
    @classmethod  
    def _update_start_site_tags(cls, chr_list):
        '''
        If the start of a tag is within 1kb of the 
        start (if + strand) or the start of a tag is within
        1kb of the end (if - strand) of the region,
        mark as a start_site.
        '''
        for chr_id in chr_list:
            for distance in (200,1000):
                update_sql = """
                UPDATE "%s" tag_seq
                SET start_site_%d = 1
                FROM "%s_%d" tag, "%s" reg
                WHERE 
                tag_seq.glass_tag_id = tag.id
                AND tag_seq.sequence_transcription_region_id = reg.id 
                AND tag.start_end && reg.start_site_%d;
                """ % (cls._meta.db_table, 
                       distance,
                       GlassTag._meta.db_table, chr_id,
                       SequenceTranscriptionRegion._meta.db_table,
                       distance)
                execute_query(update_sql)
        
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
            FROM "%s_%d" tag, "%s" ex
            WHERE
                tag_seq.glass_tag_id = tag.id
                AND tag_seq.sequence_transcription_region_id = ex.sequence_transcription_region_id
                AND tag.start_end && ex.start_end;
            """ % (cls._meta.db_table, 
                   GlassTag._meta.db_table, chr_id,
                   SequenceExon._meta.db_table)
            execute_query(update_sql)
        
class GlassTagNonCoding(GlassTagTranscriptionRegionTable):
    '''
    Relationship between GlassTag and the non coding region it maps to.
    '''
    non_coding_transcription_region = models.ForeignKey(NonCodingTranscriptionRegion)
    
    table_type = 'non_coding'
    related_class = NonCodingTranscriptionRegion
    partitioned     = False
    
    @classmethod
    def _insert_matching_tags(cls, chr_list):
        '''
        Overwritten to be strand specific
        '''
        for chr_id in chr_list:
            insert_sql = """
            INSERT INTO
                "%s" (glass_tag_id, %s_transcription_region_id)
            SELECT tag.id, reg.id
            FROM "%s_%d" tag, "%s" reg
            WHERE reg.chromosome_id = %d
                AND reg.strand = tag.strand
                AND tag.start_end && reg.start_end;
            """ % (cls._meta.db_table, cls.table_type,
                   GlassTag._meta.db_table, chr_id,
                   cls.related_class._meta.db_table,
                   chr_id)
            execute_query(insert_sql)

class GlassTagPatterned(GlassTagTranscriptionRegionTable):
    '''
    Relationship between GlassTag and the patterned region it maps to.
    '''
    patterned_transcription_region  = models.ForeignKey(PatternedTranscriptionRegion)
    
    table_type      = 'patterned'
    related_class   = PatternedTranscriptionRegion
    partitioned     = True
    
class GlassTagConserved(GlassTagTranscriptionRegionTable):
    '''
    Relationship between GlassTag and the conservation region it maps to.
    '''
    conserved_transcription_region  = models.ForeignKey(ConservedTranscriptionRegion)
    
    table_type      = 'conserved'
    related_class   = ConservedTranscriptionRegion
    partitioned     = True
    