'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcript tables.
'''

genome = 'mm10'
sql = """
CREATE TABLE "glass_atlas_%s"."glass_transcript_all" (
    "id" int4 NOT NULL,
    "chromosome_id" int4 DEFAULT NULL,
    "strand" int2 DEFAULT NULL,
    "transcription_start" int8 DEFAULT NULL,
    "transcription_end" int8 DEFAULT NULL,
    "start_end" "public"."cube" DEFAULT NULL,
    "spliced" boolean DEFAULT NULL,
    "score" numeric DEFAULT NULL,
    "modified" timestamp(6) NULL DEFAULT NULL,
    "created" timestamp(6) NULL DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s"."glass_transcript_all" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."glass_transcript_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."glass_transcript_id_seq" OWNED BY "glass_atlas_%s"."glass_transcript_all".id;
ALTER TABLE "glass_atlas_%s"."glass_transcript_all" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."glass_transcript_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."glass_transcript_all" ADD CONSTRAINT glass_transcript_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcript_chr_idx ON "glass_atlas_%s"."glass_transcript_all" USING btree (chromosome_id);
CREATE INDEX glass_transcript_start_idx ON "glass_atlas_%s"."glass_transcript_all" USING btree (transcription_start);
CREATE INDEX glass_transcript_end_idx ON "glass_atlas_%s"."glass_transcript_all" USING btree (transcription_end);
CREATE INDEX glass_transcript_start_end_idx ON "glass_atlas_%s"."glass_transcript_all" USING gist (start_end);

CREATE VIEW "glass_atlas_%s"."glass_transcript" AS SELECT * FROM "glass_atlas_%s"."glass_transcript_all" WHERE score >= 1.4;

CREATE TABLE "glass_atlas_%s"."glass_transcribed_rna" (
    "id" int4 NOT NULL,
    "glass_transcript_id" int4 DEFAULT NULL,
    "chromosome_id" int4 DEFAULT NULL,
    "start" int8 DEFAULT NULL,
    "end" int8 DEFAULT NULL,
    "start_end" "public"."cube" DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s"."glass_transcribed_rna" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."glass_transcribed_rna_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."glass_transcribed_rna_id_seq" OWNED BY "glass_atlas_%s"."glass_transcribed_rna".id;
ALTER TABLE "glass_atlas_%s"."glass_transcribed_rna" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."glass_transcribed_rna_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."glass_transcribed_rna" ADD CONSTRAINT glass_transcribed_rna_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcribed_rna_transcript_idx ON "glass_atlas_%s"."glass_transcribed_rna" USING btree (glass_transcript_id);
CREATE INDEX glass_transcribed_rna_start_idx ON "glass_atlas_%s"."glass_transcribed_rna" USING btree (start);
CREATE INDEX glass_transcribed_rna_end_idx ON "glass_atlas_%s"."glass_transcribed_rna" USING btree ("end");
CREATE INDEX glass_transcribed_rna_start_end_idx ON "glass_atlas_%s"."glass_transcribed_rna" USING gist (start_end);


CREATE TABLE "glass_atlas_%s"."glass_transcript_nucleotides" (
    "id" int4 NOT NULL,
    "glass_transcript_id" int4 DEFAULT NULL,
    "sequence" text DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s"."glass_transcript_nucleotides" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."glass_transcript_nucleotides_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."glass_transcript_nucleotides_id_seq" OWNED BY "glass_atlas_%s"."glass_transcript_nucleotides".id;
ALTER TABLE "glass_atlas_%s"."glass_transcript_nucleotides" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."glass_transcript_nucleotides_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."glass_transcript_nucleotides" ADD CONSTRAINT glass_transcript_nucleotides_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcript_nucleotides_transcript_idx ON "glass_atlas_%s"."glass_transcript_nucleotides" USING btree (glass_transcript_id);



CREATE TABLE "glass_atlas_%s"."glass_transcript_source" (
    "id" int4 NOT NULL,
    "glass_transcript_id" int4 DEFAULT NULL,
    "sequencing_run_id" int4 DEFAULT NULL,
    "tag_count" int4 DEFAULT NULL,
    "gaps" int4 DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s"."glass_transcript_source" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."glass_transcript_source_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."glass_transcript_source_id_seq" OWNED BY "glass_atlas_%s"."glass_transcript_source".id;
ALTER TABLE "glass_atlas_%s"."glass_transcript_source" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."glass_transcript_source_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."glass_transcript_source" ADD CONSTRAINT glass_transcript_source_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcript_source_transcript_idx ON "glass_atlas_%s"."glass_transcript_source" USING btree (glass_transcript_id);


CREATE TYPE "glass_atlas_%s"."glass_transcript_transcription_region_relationship" 
    AS ENUM('contains','is contained by','overlaps with','is equal to');
    
CREATE TABLE "glass_atlas_%s"."glass_transcript_sequence" (
    id integer NOT NULL,
    glass_transcript_id integer,
    sequence_transcription_region_id integer,
    relationship "glass_atlas_%s"."glass_transcript_transcription_region_relationship"
);
GRANT ALL ON TABLE "glass_atlas_%s"."glass_transcript_sequence" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."glass_transcript_sequence_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."glass_transcript_sequence_id_seq" OWNED BY "glass_atlas_%s"."glass_transcript_sequence".id;
ALTER TABLE "glass_atlas_%s"."glass_transcript_sequence" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."glass_transcript_sequence_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."glass_transcript_sequence" ADD CONSTRAINT glass_transcript_sequence_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcript_sequence_transcript_idx ON "glass_atlas_%s"."glass_transcript_sequence" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s"."glass_transcript_non_coding" (
    id integer NOT NULL,
    glass_transcript_id integer,
    non_coding_transcription_region_id integer,
    relationship "glass_atlas_%s"."glass_transcript_transcription_region_relationship"
);
GRANT ALL ON TABLE "glass_atlas_%s"."glass_transcript_non_coding" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."glass_transcript_non_coding_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."glass_transcript_non_coding_id_seq" OWNED BY "glass_atlas_%s"."glass_transcript_non_coding".id;
ALTER TABLE "glass_atlas_%s"."glass_transcript_non_coding" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."glass_transcript_non_coding_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."glass_transcript_non_coding" ADD CONSTRAINT glass_transcript_non_coding_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcript_non_coding_transcript_idx ON "glass_atlas_%s"."glass_transcript_non_coding" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s"."glass_transcript_conserved" (
    id integer NOT NULL,
    glass_transcript_id integer,
    conserved_transcription_region_id integer,
    relationship "glass_atlas_%s"."glass_transcript_transcription_region_relationship"
);
GRANT ALL ON TABLE "glass_atlas_%s"."glass_transcript_conserved" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."glass_transcript_conserved_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."glass_transcript_conserved_id_seq" OWNED BY "glass_atlas_%s"."glass_transcript_conserved".id;
ALTER TABLE "glass_atlas_%s"."glass_transcript_conserved" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."glass_transcript_conserved_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."glass_transcript_conserved" ADD CONSTRAINT glass_transcript_conserved_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcript_conserved_transcript_idx ON "glass_atlas_%s"."glass_transcript_conserved" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s"."glass_transcript_patterned" (
    id integer NOT NULL,
    glass_transcript_id integer,
    patterned_transcription_region_id integer,
    relationship "glass_atlas_%s"."glass_transcript_transcription_region_relationship"
);
GRANT ALL ON TABLE "glass_atlas_%s"."glass_transcript_patterned" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."glass_transcript_patterned_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."glass_transcript_patterned_id_seq" OWNED BY "glass_atlas_%s"."glass_transcript_patterned".id;
ALTER TABLE "glass_atlas_%s"."glass_transcript_patterned" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."glass_transcript_patterned_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."glass_transcript_patterned" ADD CONSTRAINT glass_transcript_patterned_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcript_patterned_transcript_idx ON "glass_atlas_%s"."glass_transcript_patterned" USING btree (glass_transcript_id);






CREATE TYPE "glass_atlas_%s"."sequencing_run_type" AS ENUM('Gro-Seq','RNA-Seq','ChIP-Seq');
CREATE TABLE "glass_atlas_%s"."sequencing_run" (
    "id" int4 NOT NULL,
    "type" glass_atlas_%s.sequencing_run_type DEFAULT NULL,
    "name" character(100) DEFAULT NULL,
    "source_table" character(100) DEFAULT NULL,
    "description" character(255) DEFAULT NULL,
    "total_tags" int8 DEFAULT NULL,
    "percent_mapped" numeric(5,2) DEFAULT NULL,
    "modified" timestamp(6) NULL DEFAULT NULL,
    "created" timestamp(6) NULL DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s"."sequencing_run" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."sequencing_run_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."sequencing_run_id_seq" OWNED BY "glass_atlas_%s"."sequencing_run".id;
ALTER TABLE "glass_atlas_%s"."sequencing_run" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."sequencing_run_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."sequencing_run" ADD CONSTRAINT sequencing_run_pkey PRIMARY KEY (id);
CREATE UNIQUE INDEX sequencing_run_source_table_idx ON "glass_atlas_%s"."sequencing_run" USING btree (source_table);
""" % tuple([genome]*96)
print sql