'''
Created on Oct 9, 2012

@author: karmel

'''
from glasslab.config import current_settings

class GlassAtlasTableGenerator(object):
    ''' Generates the SQL queries for building DB schema. '''
    genome = None
    cell_type = None
    staging = None
    user = None
    
    def __init__(self, genome=None, cell_type=None, staging=None, user=None):
        self.genome = genome or current_settings.GENOME
        self.cell_type = cell_type or current_settings.CELL_TYPE
        self.staging = staging or current_settings.STAGING
        self.user = user or current_settings.DATABASES['default']['USER']
        
    def convenience_functions(self):
        return """
        CREATE OR REPLACE FUNCTION public.make_box(x1 numeric, y1 numeric, x2 numeric, y2 numeric)
        RETURNS box AS $$
        DECLARE
            s text;
        BEGIN
            s := '((' || x1 || ',' || y1 || '),(' || x2 || ',' || y2 || '))';
            RETURN s::box;
        END;
        $$ LANGUAGE 'plpgsql';
        
        CREATE OR REPLACE FUNCTION public.make_box(x1 numeric, x2 numeric)
        RETURNS box AS $$
        DECLARE
            s text;
        BEGIN
            s := '((' || x1 || ', 0),(' || x2 || ',0))';
            RETURN s::box;
        END;
        $$ LANGUAGE 'plpgsql';
        """
    
    def schemas(self, final=False):
        s= """
        CREATE SCHEMA "glass_atlas_{0}_{1}{staging}" AUTHORIZATION "{user}";"""
    
        if not final:
            s += """
        CREATE SCHEMA "glass_atlas_{0}_{1}_prep" AUTHORIZATION "{user}";""" 
        return s.format(self.genome, self.cell_type, 
                        staging=self.staging, user=self.user)
        
    def other_tables(self):
        return """
        CREATE TABLE "glass_atlas_{0}"."sequencing_run" (
            "id" int4 NOT NULL,
            "source_table" varchar(100) DEFAULT NULL
        );
        GRANT ALL ON TABLE "glass_atlas_{0}"."sequencing_run" TO  "{user}";
        CREATE SEQUENCE "glass_atlas_{0}"."sequencing_run_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "glass_atlas_{0}"."sequencing_run_id_seq" OWNED BY "glass_atlas_{0}"."sequencing_run".id;
        ALTER TABLE "glass_atlas_{0}"."sequencing_run" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_{0}"."sequencing_run_id_seq"'::regclass);
        ALTER TABLE ONLY "glass_atlas_{0}"."sequencing_run" ADD CONSTRAINT sequencing_run_pkey PRIMARY KEY (id);
        CREATE UNIQUE INDEX sequencing_run_source_table_idx ON "glass_atlas_{0}"."sequencing_run" USING btree (source_table);
        
        """.format(self.genome, user=self.user)
        
        
    def prep_table_main_transcript(self):
        return """
        CREATE TABLE "glass_atlas_{0}_{1}_prep"."glass_transcript" (
            "id" int4 NOT NULL,
            "chromosome_id" int4 DEFAULT NULL,
            "strand" int2 DEFAULT NULL,
            "transcription_start" int8 DEFAULT NULL,
            "transcription_end" int8 DEFAULT NULL,
            "start_end" box DEFAULT NULL,
            "density" float DEFAULT NULL, -- RPKM per run, essentially. But number of bp is configurable.
            "edge" float DEFAULT NULL, -- Length of the allowed edge for joining transcripts.
            "start_density" point DEFAULT NULL,
            "density_circle" circle DEFAULT NULL,
            "refseq" boolean DEFAULT NULL
        );
        GRANT ALL ON TABLE "glass_atlas_{0}_{1}_prep"."glass_transcript" TO  "{user}";
        CREATE SEQUENCE "glass_atlas_{0}_{1}_prep"."glass_transcript_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "glass_atlas_{0}_{1}_prep"."glass_transcript_id_seq" OWNED BY "glass_atlas_{0}_{1}_prep"."glass_transcript".id;
        ALTER TABLE "glass_atlas_{0}_{1}_prep"."glass_transcript" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_{0}_{1}_prep"."glass_transcript_id_seq"'::regclass);
        ALTER TABLE ONLY "glass_atlas_{0}_{1}_prep"."glass_transcript" ADD CONSTRAINT glass_transcript_pkey PRIMARY KEY (id);
        """.format(self.genome, self.cell_type, user=self.user)
        
    def prep_table_chrom_transcript(self, chr_id):   
        return """ 
        CREATE TABLE "glass_atlas_{0}_{1}_prep"."glass_transcript_{chr_id}" (
            CHECK ( chromosome_id = {chr_id} )
        ) INHERITS ("glass_atlas_{0}_{1}_prep"."glass_transcript");
        CREATE INDEX glass_transcript_{chr_id}_pkey_idx ON "glass_atlas_{0}_{1}_prep"."glass_transcript_{chr_id}" USING btree (id);
        CREATE INDEX glass_transcript_{chr_id}_chr_idx ON "glass_atlas_{0}_{1}_prep"."glass_transcript_{chr_id}" USING btree (chromosome_id);
        CREATE INDEX glass_transcript_{chr_id}_strand_idx ON "glass_atlas_{0}_{1}_prep"."glass_transcript_{chr_id}" USING btree (strand);
        CREATE INDEX glass_transcript_{chr_id}_start_end_idx ON "glass_atlas_{0}_{1}_prep"."glass_transcript_{chr_id}" USING gist (start_end);
        CREATE INDEX glass_transcript_{chr_id}_start_density_idx ON "glass_atlas_{0}_{1}_prep"."glass_transcript_{chr_id}" USING gist (start_density);
        CREATE INDEX glass_transcript_{chr_id}_density_circle_idx ON "glass_atlas_{0}_{1}_prep"."glass_transcript_{chr_id}" USING gist (density_circle);
        """.format(self.genome, self.cell_type, chr_id=chr_id)
        
    def prep_table_trigger_transcript(self):
        return """
        CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}_prep.glass_transcript_insert_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            EXECUTE 'INSERT INTO glass_atlas_{0}_{1}_prep.glass_transcript_' || NEW.chromosome_id || ' VALUES ('
            || quote_literal(NEW.id) || ','
            || quote_literal(NEW.chromosome_id) || ','
            || quote_literal(NEW.strand) || ','
            || quote_literal(NEW.transcription_start) || ','
            || quote_literal(NEW.transcription_end) || ','
            || 'public.make_box(' || quote_literal(NEW.transcription_start) || ', 0, ' 
                || quote_literal(NEW.transcription_end) || ', 0)'
            || '),'
            || 'public.make_box(' || quote_literal((NEW.start_density[1])[0]) || ', ' || quote_literal((NEW.start_density[1])[1]) || ', ' 
                || quote_literal((NEW.start_density[0])[0]) || ', ' || quote_literal((NEW.start_density[0])[1]) || '),'
            || 'circle(' || quote_literal(center(NEW.density_circle)) || ', ' || quote_literal(radius(NEW.density_circle)) || ')'
            || '),'
            || quote_literal(NEW.refseq)
            ;
            RETURN NULL;
        END;
        $$
        LANGUAGE 'plpgsql';
        
        -- Trigger function for inserts on main table
        CREATE TRIGGER glass_transcript_trigger
            BEFORE INSERT ON "glass_atlas_{0}_{1}_prep"."glass_transcript"
            FOR EACH ROW EXECUTE PROCEDURE glass_atlas_{0}_{1}_prep.glass_transcript_insert_trigger();
        """.format(self.genome, self.cell_type)
        
    def table_main_source(self, suffix=''):
        return """
        CREATE TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source" (
            "id" int4 NOT NULL,
            "chromosome_id" int4 DEFAULT NULL,
            "glass_transcript_id" int4 DEFAULT NULL,
            "sequencing_run_id" int4 DEFAULT NULL,
            "tag_count" int4 DEFAULT NULL,
            "gaps" int4 DEFAULT NULL
        );
        GRANT ALL ON TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source" TO  "{user}";
        CREATE SEQUENCE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source_id_seq" OWNED BY "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source".id;
        ALTER TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_{0}_{1}{suffix}"."glass_transcript_source_id_seq"'::regclass);
        ALTER TABLE ONLY "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source" ADD CONSTRAINT glass_transcript_source_pkey PRIMARY KEY (id);
        """.format(self.genome, self.cell_type, user=self.user, suffix=suffix)
        
    def table_chrom_source(self, chr_id, suffix=''):
        return """
        CREATE TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source_{chr_id}" (
            CHECK ( chromosome_id = {chr_id} )
        ) INHERITS ("glass_atlas_{0}_{1}{suffix}"."glass_transcript_source");
        CREATE INDEX glass_transcript_source_{chr_id}_pkey_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source_{chr_id}" USING btree (id);
        CREATE INDEX glass_transcript_source_{chr_id}_transcript_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source_{chr_id}" USING btree (glass_transcript_id);
        CREATE INDEX glass_transcript_source_{chr_id}_sequencing_run_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source_{chr_id}" USING btree (sequencing_run_id);
        """.format(self.genome, self.cell_type, chr_id=chr_id, suffix=suffix)
        
    def table_trigger_source(self, suffix=''):
        return """
        CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}{suffix}.glass_transcript_source_insert_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            EXECUTE 'INSERT INTO glass_atlas_{0}_{1}{suffix}.glass_transcript_source_' || NEW.chromosome_id || ' VALUES ('
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
            BEFORE INSERT ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_source"
            FOR EACH ROW EXECUTE PROCEDURE glass_atlas_{0}_{1}{suffix}.glass_transcript_source_insert_trigger();
        """.format(self.genome, self.cell_type, suffix=suffix)
        
    def table_main_transcript(self):
        return """
        CREATE TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript" (
            "id" int4 NOT NULL,
            "chromosome_id" int4 DEFAULT NULL,
            "strand" int2 DEFAULT NULL,
            "transcription_start" int8 DEFAULT NULL,
            "transcription_end" int8 DEFAULT NULL,
            "start_end" box DEFAULT NULL,
            "refseq" boolean DEFAULT NULL,
            "distal" boolean DEFAULT NULL,
            "score" numeric DEFAULT NULL,
            "standard_error" numeric DEFAULT NULL,
            "modified" timestamp(6) NULL DEFAULT NULL,
            "created" timestamp(6) NULL DEFAULT NULL
        );
        GRANT ALL ON TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript" TO  "{user}";
        CREATE SEQUENCE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_id_seq" OWNED BY "glass_atlas_{0}_{1}{suffix}"."glass_transcript".id;
        ALTER TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_{0}_{1}{suffix}"."glass_transcript_id_seq"'::regclass);
        ALTER TABLE ONLY "glass_atlas_{0}_{1}{suffix}"."glass_transcript" ADD CONSTRAINT glass_transcript_pkey PRIMARY KEY (id);
        """.format(self.genome, self.cell_type, user=self.user, suffix=self.staging)
        
    
    def table_chrom_transcript(self, chr_id):
        return """
        CREATE TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_1" (
            CHECK ( chromosome_id = 1 )
        ) INHERITS ("glass_atlas_{0}_{1}{suffix}"."glass_transcript");
        CREATE INDEX glass_transcript_1_pkey_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_1" USING btree (id);
        CREATE INDEX glass_transcript_1_chr_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_1" USING btree (chromosome_id);
        CREATE INDEX glass_transcript_1_strand_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_1" USING btree (strand);
        CREATE INDEX glass_transcript_1_score_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_1" USING btree (score);
        CREATE INDEX glass_transcript_1_distal_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_1" USING btree (distal);
        CREATE INDEX glass_transcript_1_start_end_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_1" USING gist (start_end);
        """.format(self.genome, self.cell_type, chr_id=chr_id, suffix=self.staging)
        
    def table_trigger_transcript(self):
        return """
        CREATE OR REPLACE FUNCTION glass_atlas_{0}_{1}{suffix}.glass_transcript_insert_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            EXECUTE 'INSERT INTO glass_atlas_{0}_{1}{suffix}.glass_transcript_' || NEW.chromosome_id || ' VALUES ('
            || quote_literal(NEW.id) || ','
            || quote_literal(NEW.chromosome_id) || ','
            || quote_literal(NEW.strand) || ','
            || quote_literal(NEW.transcription_start) || ','
            || quote_literal(NEW.transcription_end) || ','
            || 'public.make_box(' || quote_literal(NEW.transcription_start) || ', 0, ' 
                || quote_literal(NEW.transcription_end) || ', 0),'
            || coalesce(quote_literal(NEW.start_end_density),'NULL') || ','
            || coalesce(quote_literal(NEW.score),'NULL') || ','
            || quote_literal(NEW.modified) || ','
            || quote_literal(NEW.created) || ')';
            RETURN NULL;
        END;
        $$
        LANGUAGE 'plpgsql';
        
        -- Trigger function for inserts on main table
        CREATE TRIGGER glass_transcript_trigger
            BEFORE INSERT ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript"
            FOR EACH ROW EXECUTE PROCEDURE glass_atlas_{0}_{1}{suffix}.glass_transcript_insert_trigger();

        """.format(self.genome, self.cell_type, suffix=self.staging)
        
        
    def region_relationship_types(self):
        return """
        CREATE TYPE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_transcription_region_relationship" 
        AS ENUM('contains','is contained by','overlaps with','is equal to');
        """.format(self.genome, self.cell_type, suffix=self.staging)
        
    def table_region_association(self, region_type):
        return """
        CREATE TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}" (
            id integer NOT NULL,
            glass_transcript_id integer,
            {type}_transcription_region_id integer,
            relationship "glass_atlas_{0}_{1}{suffix}"."glass_transcript_transcription_region_relationship",
            major boolean
        );
        GRANT ALL ON TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}" TO  "glass";
        CREATE SEQUENCE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}_id_seq" OWNED BY "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}".id;
        ALTER TABLE "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}_id_seq"'::regclass);
        ALTER TABLE ONLY "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}" ADD CONSTRAINT glass_transcript_{type}_pkey PRIMARY KEY (id);
        CREATE INDEX glass_transcript_{type}_transcript_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}" USING btree (glass_transcript_id);
        CREATE INDEX glass_transcript_{type}_major_idx ON "glass_atlas_{0}_{1}{suffix}"."glass_transcript_{type}" USING btree (major);
        """.format(self.genome, self.cell_type, type=region_type, suffix=self.staging)