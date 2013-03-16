'''
Created on Oct 9, 2012

@author: karmel

'''
from glasslab.config import current_settings
from glasslab.glassatlas.sql import transcripts_from_prep_functions,\
    transcripts_from_tags_functions
from glasslab.utils.database import SqlGenerator

class GlassAtlasSqlGenerator(SqlGenerator):
    ''' Generates the SQL queries for building DB schema. '''
    genome = None
    cell_type = None
    staging = None
    
    def __init__(self, genome=None, cell_type=None, staging=None, user=None):
        self.genome = genome or current_settings.GENOME.lower()
        self.cell_type = cell_type or current_settings.CELL_TYPE.lower()
        self.staging = staging or current_settings.STAGING
        
        self.schema_name_prefix = 'glass_atlas_{0}_{1}'.format(self.genome, self.cell_type)
        super(GlassAtlasSqlGenerator, self).__init__()
    
    def all_sql(self):
        return self.prep_set() + self.final_set()
    
    def prep_set(self):
        prep_suffix = '_prep'
        s = self.schema(prep_suffix)
        s += self.prep_table_main_transcript()
        s += self.table_main_source(prep_suffix)
        
        for chr_id in current_settings.GENOME_CHOICES[current_settings.GENOME]['chromosomes']:
            s += self.prep_table_chrom_transcript(chr_id)
            s += self.table_chrom_source(chr_id, prep_suffix)
        
        s += self.prep_table_trigger_transcript()
        s += self.table_trigger_source(prep_suffix)
        
        s += self.from_tags_functions()  
        return s
            
    def final_set(self):
        s = self.schema(self.staging)
        s += self.table_main_transcript()
        s += self.table_main_source(self.staging)
        for chr_id in current_settings.GENOME_CHOICES[current_settings.GENOME]['chromosomes']:
            s += self.table_chrom_transcript(chr_id)
            s += self.table_chrom_source(chr_id, self.staging)
        
        s += self.table_trigger_transcript()
        s += self.table_trigger_source(self.staging)
        
        s += self.region_relationship_types()
        s += self.table_region_association('sequence')
        s += self.table_region_association('non_coding')
        
        s += self.from_prep_functions()
        
        return s
    
    # Functions
    def from_tags_functions(self):
        return transcripts_from_tags_functions.sql(self.genome, self.cell_type)
    
    def from_prep_functions(self):
        return transcripts_from_prep_functions.sql(self.genome, self.cell_type, self.staging)
    
    # Tables
    def schema(self, suffix=''):
        return """
        CREATE SCHEMA "{schema_name_prefix}{suffix}" AUTHORIZATION "{user}";
        """.format(schema_name_prefix=self.schema_name_prefix, suffix=suffix, user=self.user)
        
    def prep_table_main_transcript(self):
        table_name = 'glass_transcript'
        return """
        CREATE TABLE "{schema_name_prefix}_prep"."{table_name}" (
            "id" int4 NOT NULL,
            "chromosome_id" int4 DEFAULT NULL,
            "strand" int2 DEFAULT NULL,
            "transcription_start" int8 DEFAULT NULL,
            "transcription_end" int8 DEFAULT NULL,
            "start_end" int8range DEFAULT NULL,
            "density" float DEFAULT NULL, -- RPKM per run, essentially. But number of bp is configurable.
            "edge" float DEFAULT NULL, -- Length of the allowed edge for joining transcripts.
            "start_density" point DEFAULT NULL,
            "density_circle" circle DEFAULT NULL,
            "refseq" boolean DEFAULT NULL
        );
        """.format(schema_name_prefix=self.schema_name_prefix, table_name=table_name, user=self.user)\
        + self.pkey_sequence_sql(self.schema_name_prefix + '_prep', table_name)
        
    def prep_table_chrom_transcript(self, chr_id):   
        return """ 
        CREATE TABLE "{schema_name_prefix}_prep"."glass_transcript_{chr_id}" (
            CHECK ( chromosome_id = {chr_id} )
        ) INHERITS ("{schema_name_prefix}_prep"."glass_transcript");
        CREATE INDEX glass_transcript_{chr_id}_pkey_idx ON "{schema_name_prefix}_prep"."glass_transcript_{chr_id}" USING btree (id);
        CREATE INDEX glass_transcript_{chr_id}_chr_idx ON "{schema_name_prefix}_prep"."glass_transcript_{chr_id}" USING btree (chromosome_id);
        CREATE INDEX glass_transcript_{chr_id}_strand_idx ON "{schema_name_prefix}_prep"."glass_transcript_{chr_id}" USING btree (strand);
        CREATE INDEX glass_transcript_{chr_id}_start_end_idx ON "{schema_name_prefix}_prep"."glass_transcript_{chr_id}" USING gist (start_end);
        CREATE INDEX glass_transcript_{chr_id}_start_density_idx ON "{schema_name_prefix}_prep"."glass_transcript_{chr_id}" USING gist (start_density);
        CREATE INDEX glass_transcript_{chr_id}_density_circle_idx ON "{schema_name_prefix}_prep"."glass_transcript_{chr_id}" USING gist (density_circle);
        """.format(schema_name_prefix=self.schema_name_prefix, chr_id=chr_id)
        
    def prep_table_trigger_transcript(self):
        return """
        CREATE OR REPLACE FUNCTION {schema_name_prefix}_prep.glass_transcript_insert_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            EXECUTE 'INSERT INTO {schema_name_prefix}_prep.glass_transcript_' || NEW.chromosome_id || ' VALUES ('
            || quote_literal(NEW.id) || ','
            || quote_literal(NEW.chromosome_id) || ','
            || quote_literal(NEW.strand) || ','
            || quote_literal(NEW.transcription_start) || ','
            || quote_literal(NEW.transcription_end) || ','
            || 'int8range(' || quote_literal(NEW.transcription_start) || ', ''[]''), ' 
                || quote_literal(NEW.transcription_end) || ')'
            || '),'
            || quote_literal(NEW.density) || ','
            || quote_literal(NEW.edge) || ','
            || 'point(' || quote_literal(NEW.transcription_start) || ', ' || quote_literal(NEW.density) || '),'
            || 'circle(' || quote_literal(center(NEW.density_circle)) || ', ' || quote_literal(radius(NEW.density_circle)) || '),'
            || quote_literal(NEW.refseq)
            || ')'
            ;
            RETURN NULL;
        END;
        $$
        LANGUAGE 'plpgsql';
        
        -- Trigger function for inserts on main table
        CREATE TRIGGER glass_transcript_trigger
            BEFORE INSERT ON "{schema_name_prefix}_prep"."glass_transcript"
            FOR EACH ROW EXECUTE PROCEDURE {schema_name_prefix}_prep.glass_transcript_insert_trigger();
        """.format(schema_name_prefix=self.schema_name_prefix)
        
    def table_main_source(self, suffix=''):
        table_name = 'glass_transcript_source'
        return """
        CREATE TABLE "{schema_name_prefix}{suffix}"."{table_name}" (
            "id" int4 NOT NULL,
            "chromosome_id" int4 DEFAULT NULL,
            "glass_transcript_id" int4 DEFAULT NULL,
            "sequencing_run_id" int4 DEFAULT NULL,
            "tag_count" int4 DEFAULT NULL,
            "gaps" int4 DEFAULT NULL
        );
        """.format(schema_name_prefix=self.schema_name_prefix, table_name=table_name, suffix=suffix)\
        + self.pkey_sequence_sql(self.schema_name_prefix + suffix, table_name)
        
    def table_chrom_source(self, chr_id, suffix=''):
        return """
        CREATE TABLE "{schema_name_prefix}{suffix}"."glass_transcript_source_{chr_id}" (
            CHECK ( chromosome_id = {chr_id} )
        ) INHERITS ("{schema_name_prefix}{suffix}"."glass_transcript_source");
        CREATE INDEX glass_transcript_source_{chr_id}_pkey_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_source_{chr_id}" USING btree (id);
        CREATE INDEX glass_transcript_source_{chr_id}_transcript_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_source_{chr_id}" USING btree (glass_transcript_id);
        CREATE INDEX glass_transcript_source_{chr_id}_sequencing_run_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_source_{chr_id}" USING btree (sequencing_run_id);
        """.format(schema_name_prefix=self.schema_name_prefix, chr_id=chr_id, suffix=suffix)
        
    def table_trigger_source(self, suffix=''):
        return """
        CREATE OR REPLACE FUNCTION {schema_name_prefix}{suffix}.glass_transcript_source_insert_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            EXECUTE 'INSERT INTO {schema_name_prefix}{suffix}.glass_transcript_source_' || NEW.chromosome_id || ' VALUES ('
            || quote_literal(NEW.id) || ','
            || quote_literal(NEW.chromosome_id) || ','
            || quote_literal(NEW.glass_transcript_id) || ','
            || quote_literal(NEW.sequencing_run_id) || ','
            || quote_literal(NEW.tag_count) || ','
            || quote_literal(NEW.gaps)
            || ')'
            ;
            RETURN NULL;
        END;
        $$
        LANGUAGE 'plpgsql';
        
        -- Trigger function for inserts on main table
        CREATE TRIGGER glass_transcript_source_trigger
            BEFORE INSERT ON "{schema_name_prefix}{suffix}"."glass_transcript_source"
            FOR EACH ROW EXECUTE PROCEDURE {schema_name_prefix}{suffix}.glass_transcript_source_insert_trigger();
        """.format(schema_name_prefix=self.schema_name_prefix, suffix=suffix)
        
    def table_main_transcript(self):
        table_name = 'glass_transcript'
        return """
        CREATE TABLE "{schema_name_prefix}{suffix}"."{table_name}" (
            "id" int4 NOT NULL,
            "chromosome_id" int4 DEFAULT NULL,
            "strand" int2 DEFAULT NULL,
            "transcription_start" int8 DEFAULT NULL,
            "transcription_end" int8 DEFAULT NULL,
            "start_end" int8range DEFAULT NULL,
            "start_end_tss" int8range DEFAULT NULL,
            "refseq" boolean DEFAULT NULL,
            "distal" boolean DEFAULT NULL,
            "score" numeric DEFAULT NULL,
            "rpkm" numeric DEFAULT NULL,
            "standard_error" numeric DEFAULT NULL,
            "modified" timestamp(6) NULL DEFAULT NULL,
            "created" timestamp(6) NULL DEFAULT NULL
        );
        """.format(schema_name_prefix=self.schema_name_prefix, table_name=table_name, suffix=self.staging)\
        + self.pkey_sequence_sql(self.schema_name_prefix + self.staging, table_name)
        
    
    def table_chrom_transcript(self, chr_id):
        return """
        CREATE TABLE "{schema_name_prefix}{suffix}"."glass_transcript_{chr_id}" (
            CHECK ( chromosome_id = {chr_id} )
        ) INHERITS ("{schema_name_prefix}{suffix}"."glass_transcript");
        CREATE INDEX glass_transcript_{chr_id}_pkey_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_{chr_id}" USING btree (id);
        CREATE INDEX glass_transcript_{chr_id}_chr_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_{chr_id}" USING btree (chromosome_id);
        CREATE INDEX glass_transcript_{chr_id}_strand_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_{chr_id}" USING btree (strand);
        CREATE INDEX glass_transcript_{chr_id}_score_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_{chr_id}" USING btree (score);
        CREATE INDEX glass_transcript_{chr_id}_distal_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_{chr_id}" USING btree (distal);
        CREATE INDEX glass_transcript_{chr_id}_start_end_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_{chr_id}" USING gist (start_end);
        CREATE INDEX glass_transcript_{chr_id}_start_end_tss_idx ON "{schema_name_prefix}{suffix}"."glass_transcript_{chr_id}" USING gist (start_end_tss);
        """.format(schema_name_prefix=self.schema_name_prefix, chr_id=chr_id, suffix=self.staging)
        
    def table_trigger_transcript(self):
        return """
        CREATE OR REPLACE FUNCTION {schema_name_prefix}{suffix}.glass_transcript_insert_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            EXECUTE 'INSERT INTO {schema_name_prefix}{suffix}.glass_transcript_' || NEW.chromosome_id || ' VALUES ('
            || quote_literal(NEW.id) || ','
            || quote_literal(NEW.chromosome_id) || ','
            || quote_literal(NEW.strand) || ','
            || quote_literal(NEW.transcription_start) || ','
            || quote_literal(NEW.transcription_end) || ','
            || 'int8range(' || quote_literal(NEW.transcription_start) || ', ''[]''),' 
                || quote_literal(NEW.transcription_end) || '),'
            || 'NULL,' 
            || coalesce(quote_literal(NEW.refseq),'NULL') || ','
            || coalesce(quote_literal(NEW.distal),'NULL') || ','
            || coalesce(quote_literal(NEW.score),'NULL') || ','
            || coalesce(quote_literal(NEW.rpkm),'NULL') || ','
            || coalesce(quote_literal(NEW.standard_error),'NULL') || ','
            || quote_literal(NEW.modified) || ','
            || quote_literal(NEW.created) || ')';
            RETURN NULL;
        END;
        $$
        LANGUAGE 'plpgsql';
        
        -- Trigger function for inserts on main table
        CREATE TRIGGER glass_transcript_trigger
            BEFORE INSERT ON "{schema_name_prefix}{suffix}"."glass_transcript"
            FOR EACH ROW EXECUTE PROCEDURE {schema_name_prefix}{suffix}.glass_transcript_insert_trigger();

        """.format(schema_name_prefix=self.schema_name_prefix, suffix=self.staging)
        
        
    def region_relationship_types(self):
        return """
        CREATE TYPE "{schema_name_prefix}{suffix}"."glass_transcript_transcription_region_relationship" 
        AS ENUM('contains','is contained by','overlaps with','is equal to');
        """.format(schema_name_prefix=self.schema_name_prefix, suffix=self.staging)
        
    def table_region_association(self, region_type):
        table_name = 'glass_transcript_{type}'.format(type=region_type)
        return """
        CREATE TABLE "{schema_name_prefix}{suffix}"."{table_name}" (
            id integer NOT NULL,
            glass_transcript_id integer,
            {type}_transcription_region_id integer,
            relationship "{schema_name_prefix}{suffix}"."glass_transcript_transcription_region_relationship",
            major boolean
        );
        CREATE INDEX {table_name}_transcript_idx ON "{schema_name_prefix}{suffix}"."{table_name}" USING btree (glass_transcript_id);
        CREATE INDEX {table_name}_major_idx ON "{schema_name_prefix}{suffix}"."{table_name}" USING btree (major);
        """.format(schema_name_prefix=self.schema_name_prefix, 
                   table_name=table_name, suffix=self.staging, type=region_type) \
        + self.pkey_sequence_sql(self.schema_name_prefix + self.staging, table_name)
        
    
    