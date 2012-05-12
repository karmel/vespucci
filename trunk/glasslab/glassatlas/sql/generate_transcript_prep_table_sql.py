'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcript tables.
'''

genome = 'mm9'
cell_type = 'thiomac'
def sql(genome, cell_type):
    return """
CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript" (
    "id" int4 NOT NULL,
    "chromosome_id" int4 DEFAULT NULL,
    "strand" int2 DEFAULT NULL,
    "transcription_start" int8 DEFAULT NULL,
    "transcription_end" int8 DEFAULT NULL,
    "start_end" box DEFAULT NULL,
    "start_density" point DEFAULT NULL,
    "density_circle" circle DEFAULT NULL,
    "refseq" boolean DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s_prep"."glass_transcript" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s_prep"."glass_transcript_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s_prep"."glass_transcript_id_seq" OWNED BY "glass_atlas_%s_%s_prep"."glass_transcript".id;
ALTER TABLE "glass_atlas_%s_%s_prep"."glass_transcript" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s_prep"."glass_transcript_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s_prep"."glass_transcript" ADD CONSTRAINT glass_transcript_pkey PRIMARY KEY (id);

-- Tables for each chromosome
CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_1" (
    CHECK ( chromosome_id = 1 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_1_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_1" USING btree (id);
CREATE INDEX glass_transcript_1_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_1" USING btree (chromosome_id);
CREATE INDEX glass_transcript_1_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_1" USING btree (strand);
CREATE INDEX glass_transcript_1_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_1" USING gist (start_end);
CREATE INDEX glass_transcript_1_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_1" USING gist (start_density);
CREATE INDEX glass_transcript_1_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_1" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_2" (
    CHECK ( chromosome_id = 2 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_2_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_2" USING btree (id);
CREATE INDEX glass_transcript_2_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_2" USING btree (chromosome_id);
CREATE INDEX glass_transcript_2_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_2" USING btree (strand);
CREATE INDEX glass_transcript_2_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_2" USING gist (start_end);
CREATE INDEX glass_transcript_2_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_2" USING gist (start_density);
CREATE INDEX glass_transcript_2_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_2" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_3" (
    CHECK ( chromosome_id = 3 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_3_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_3" USING btree (id);
CREATE INDEX glass_transcript_3_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_3" USING btree (chromosome_id);
CREATE INDEX glass_transcript_3_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_3" USING btree (strand);
CREATE INDEX glass_transcript_3_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_3" USING gist (start_end);
CREATE INDEX glass_transcript_3_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_3" USING gist (start_density);
CREATE INDEX glass_transcript_3_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_3" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_4" (
    CHECK ( chromosome_id = 4 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_4_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_4" USING btree (id);
CREATE INDEX glass_transcript_4_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_4" USING btree (chromosome_id);
CREATE INDEX glass_transcript_4_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_4" USING btree (strand);
CREATE INDEX glass_transcript_4_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_4" USING gist (start_end);
CREATE INDEX glass_transcript_4_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_4" USING gist (start_density);
CREATE INDEX glass_transcript_4_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_4" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_5" (
    CHECK ( chromosome_id = 5 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_5_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_5" USING btree (id);
CREATE INDEX glass_transcript_5_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_5" USING btree (chromosome_id);
CREATE INDEX glass_transcript_5_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_5" USING btree (strand);
CREATE INDEX glass_transcript_5_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_5" USING gist (start_end);
CREATE INDEX glass_transcript_5_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_5" USING gist (start_density);
CREATE INDEX glass_transcript_5_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_5" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_6" (
    CHECK ( chromosome_id = 6 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_6_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_6" USING btree (id);
CREATE INDEX glass_transcript_6_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_6" USING btree (chromosome_id);
CREATE INDEX glass_transcript_6_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_6" USING btree (strand);
CREATE INDEX glass_transcript_6_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_6" USING gist (start_end);
CREATE INDEX glass_transcript_6_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_6" USING gist (start_density);
CREATE INDEX glass_transcript_6_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_6" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_7" (
    CHECK ( chromosome_id = 7 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_7_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_7" USING btree (id);
CREATE INDEX glass_transcript_7_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_7" USING btree (chromosome_id);
CREATE INDEX glass_transcript_7_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_7" USING btree (strand);
CREATE INDEX glass_transcript_7_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_7" USING gist (start_end);
CREATE INDEX glass_transcript_7_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_7" USING gist (start_density);
CREATE INDEX glass_transcript_7_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_7" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_8" (
    CHECK ( chromosome_id = 8 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_8_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_8" USING btree (id);
CREATE INDEX glass_transcript_8_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_8" USING btree (chromosome_id);
CREATE INDEX glass_transcript_8_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_8" USING btree (strand);
CREATE INDEX glass_transcript_8_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_8" USING gist (start_end);
CREATE INDEX glass_transcript_8_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_8" USING gist (start_density);
CREATE INDEX glass_transcript_8_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_8" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_9" (
    CHECK ( chromosome_id = 9 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_9_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_9" USING btree (id);
CREATE INDEX glass_transcript_9_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_9" USING btree (chromosome_id);
CREATE INDEX glass_transcript_9_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_9" USING btree (strand);
CREATE INDEX glass_transcript_9_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_9" USING gist (start_end);
CREATE INDEX glass_transcript_9_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_9" USING gist (start_density);
CREATE INDEX glass_transcript_9_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_9" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_10" (
    CHECK ( chromosome_id = 10 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_10_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_10" USING btree (id);
CREATE INDEX glass_transcript_10_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_10" USING btree (chromosome_id);
CREATE INDEX glass_transcript_10_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_10" USING btree (strand);
CREATE INDEX glass_transcript_10_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_10" USING gist (start_end);
CREATE INDEX glass_transcript_10_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_10" USING gist (start_density);
CREATE INDEX glass_transcript_10_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_10" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_11" (
    CHECK ( chromosome_id = 11 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_11_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_11" USING btree (id);
CREATE INDEX glass_transcript_11_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_11" USING btree (chromosome_id);
CREATE INDEX glass_transcript_11_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_11" USING btree (strand);
CREATE INDEX glass_transcript_11_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_11" USING gist (start_end);
CREATE INDEX glass_transcript_11_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_11" USING gist (start_density);
CREATE INDEX glass_transcript_11_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_11" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_12" (
    CHECK ( chromosome_id = 12 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_12_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_12" USING btree (id);
CREATE INDEX glass_transcript_12_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_12" USING btree (chromosome_id);
CREATE INDEX glass_transcript_12_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_12" USING btree (strand);
CREATE INDEX glass_transcript_12_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_12" USING gist (start_end);
CREATE INDEX glass_transcript_12_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_12" USING gist (start_density);
CREATE INDEX glass_transcript_12_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_12" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_13" (
    CHECK ( chromosome_id = 13 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_13_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_13" USING btree (id);
CREATE INDEX glass_transcript_13_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_13" USING btree (chromosome_id);
CREATE INDEX glass_transcript_13_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_13" USING btree (strand);
CREATE INDEX glass_transcript_13_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_13" USING gist (start_end);
CREATE INDEX glass_transcript_13_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_13" USING gist (start_density);
CREATE INDEX glass_transcript_13_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_13" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_14" (
    CHECK ( chromosome_id = 14 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_14_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_14" USING btree (id);
CREATE INDEX glass_transcript_14_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_14" USING btree (chromosome_id);
CREATE INDEX glass_transcript_14_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_14" USING btree (strand);
CREATE INDEX glass_transcript_14_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_14" USING gist (start_end);
CREATE INDEX glass_transcript_14_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_14" USING gist (start_density);
CREATE INDEX glass_transcript_14_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_14" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_15" (
    CHECK ( chromosome_id = 15 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_15_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_15" USING btree (id);
CREATE INDEX glass_transcript_15_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_15" USING btree (chromosome_id);
CREATE INDEX glass_transcript_15_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_15" USING btree (strand);
CREATE INDEX glass_transcript_15_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_15" USING gist (start_end);
CREATE INDEX glass_transcript_15_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_15" USING gist (start_density);
CREATE INDEX glass_transcript_15_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_15" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_16" (
    CHECK ( chromosome_id = 16 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_16_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_16" USING btree (id);
CREATE INDEX glass_transcript_16_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_16" USING btree (chromosome_id);
CREATE INDEX glass_transcript_16_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_16" USING btree (strand);
CREATE INDEX glass_transcript_16_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_16" USING gist (start_end);
CREATE INDEX glass_transcript_16_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_16" USING gist (start_density);
CREATE INDEX glass_transcript_16_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_16" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_17" (
    CHECK ( chromosome_id = 17 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_17_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_17" USING btree (id);
CREATE INDEX glass_transcript_17_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_17" USING btree (chromosome_id);
CREATE INDEX glass_transcript_17_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_17" USING btree (strand);
CREATE INDEX glass_transcript_17_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_17" USING gist (start_end);
CREATE INDEX glass_transcript_17_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_17" USING gist (start_density);
CREATE INDEX glass_transcript_17_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_17" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_18" (
    CHECK ( chromosome_id = 18 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_18_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_18" USING btree (id);
CREATE INDEX glass_transcript_18_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_18" USING btree (chromosome_id);
CREATE INDEX glass_transcript_18_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_18" USING btree (strand);
CREATE INDEX glass_transcript_18_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_18" USING gist (start_end);
CREATE INDEX glass_transcript_18_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_18" USING gist (start_density);
CREATE INDEX glass_transcript_18_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_18" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_19" (
    CHECK ( chromosome_id = 19 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_19_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_19" USING btree (id);
CREATE INDEX glass_transcript_19_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_19" USING btree (chromosome_id);
CREATE INDEX glass_transcript_19_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_19" USING btree (strand);
CREATE INDEX glass_transcript_19_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_19" USING gist (start_end);
CREATE INDEX glass_transcript_19_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_19" USING gist (start_density);
CREATE INDEX glass_transcript_19_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_19" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_20" (
    CHECK ( chromosome_id = 20 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_20_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_20" USING btree (id);
CREATE INDEX glass_transcript_20_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_20" USING btree (chromosome_id);
CREATE INDEX glass_transcript_20_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_20" USING btree (strand);
CREATE INDEX glass_transcript_20_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_20" USING gist (start_end);
CREATE INDEX glass_transcript_20_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_20" USING gist (start_density);
CREATE INDEX glass_transcript_20_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_20" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_21" (
    CHECK ( chromosome_id = 21 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_21_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_21" USING btree (id);
CREATE INDEX glass_transcript_21_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_21" USING btree (chromosome_id);
CREATE INDEX glass_transcript_21_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_21" USING btree (strand);
CREATE INDEX glass_transcript_21_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_21" USING gist (start_end);
CREATE INDEX glass_transcript_21_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_21" USING gist (start_density);
CREATE INDEX glass_transcript_21_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_21" USING gist (density_circle);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_22" (
    CHECK ( chromosome_id = 22 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript");
CREATE INDEX glass_transcript_22_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_22" USING btree (id);
CREATE INDEX glass_transcript_22_chr_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_22" USING btree (chromosome_id);
CREATE INDEX glass_transcript_22_strand_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_22" USING btree (strand);
CREATE INDEX glass_transcript_22_start_end_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_22" USING gist (start_end);
CREATE INDEX glass_transcript_22_start_density_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_22" USING gist (start_density);
CREATE INDEX glass_transcript_22_density_circle_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_22" USING gist (density_circle);

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.glass_transcript_insert_trigger()
RETURNS TRIGGER AS $$
BEGIN
    EXECUTE 'INSERT INTO glass_atlas_%s_%s_prep.glass_transcript_' || NEW.chromosome_id || ' VALUES ('
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
    BEFORE INSERT ON "glass_atlas_%s_%s_prep"."glass_transcript"
    FOR EACH ROW EXECUTE PROCEDURE glass_atlas_%s_%s_prep.glass_transcript_insert_trigger();




CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source" (
    "id" int4 NOT NULL,
    "chromosome_id" int4 DEFAULT NULL,
    "glass_transcript_id" int4 DEFAULT NULL,
    "sequencing_run_id" int4 DEFAULT NULL,
    "tag_count" int4 DEFAULT NULL,
    "gaps" int4 DEFAULT NULL,
    "polya_count" int4 DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s_prep"."glass_transcript_source_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s_prep"."glass_transcript_source_id_seq" OWNED BY "glass_atlas_%s_%s_prep"."glass_transcript_source".id;
ALTER TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s_prep"."glass_transcript_source_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s_prep"."glass_transcript_source" ADD CONSTRAINT glass_transcript_source_pkey PRIMARY KEY (id);

CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_1" (
    CHECK ( chromosome_id = 1 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_1_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_1" USING btree (id);
CREATE INDEX glass_transcript_source_1_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_1" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_1_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_1" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_2" (
    CHECK ( chromosome_id = 2 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_2_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_2" USING btree (id);
CREATE INDEX glass_transcript_source_2_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_2" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_2_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_2" USING btree (sequencing_run_id);
CREATE INDEX glass_transcript_source_2_tag_count_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_2" USING btree (tag_count);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_3" (
    CHECK ( chromosome_id = 3 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_3_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_3" USING btree (id);
CREATE INDEX glass_transcript_source_3_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_3" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_3_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_3" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_4" (
    CHECK ( chromosome_id = 4 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_4_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_4" USING btree (id);
CREATE INDEX glass_transcript_source_4_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_4" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_4_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_4" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_5" (
    CHECK ( chromosome_id = 5 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_5_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_5" USING btree (id);
CREATE INDEX glass_transcript_source_5_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_5" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_5_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_5" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_6" (
    CHECK ( chromosome_id = 6 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_6_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_6" USING btree (id);
CREATE INDEX glass_transcript_source_6_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_6" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_6_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_6" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_7" (
    CHECK ( chromosome_id = 7 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_7_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_7" USING btree (id);
CREATE INDEX glass_transcript_source_7_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_7" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_7_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_7" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_8" (
    CHECK ( chromosome_id = 8 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_8_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_8" USING btree (id);
CREATE INDEX glass_transcript_source_8_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_8" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_8_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_8" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_9" (
    CHECK ( chromosome_id = 9 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_9_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_9" USING btree (id);
CREATE INDEX glass_transcript_source_9_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_9" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_9_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_9" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_10" (
    CHECK ( chromosome_id = 10 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_10_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_10" USING btree (id);
CREATE INDEX glass_transcript_source_10_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_10" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_10_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_10" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_11" (
    CHECK ( chromosome_id = 11 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_11_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_11" USING btree (id);
CREATE INDEX glass_transcript_source_11_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_11" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_11_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_11" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_12" (
    CHECK ( chromosome_id = 12 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_12_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_12" USING btree (id);
CREATE INDEX glass_transcript_source_12_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_12" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_12_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_12" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_13" (
    CHECK ( chromosome_id = 13 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_13_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_13" USING btree (id);
CREATE INDEX glass_transcript_source_13_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_13" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_13_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_13" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_14" (
    CHECK ( chromosome_id = 14 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_14_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_14" USING btree (id);
CREATE INDEX glass_transcript_source_14_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_14" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_14_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_14" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_15" (
    CHECK ( chromosome_id = 15 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_15_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_15" USING btree (id);
CREATE INDEX glass_transcript_source_15_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_15" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_15_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_15" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_16" (
    CHECK ( chromosome_id = 16 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_16_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_16" USING btree (id);
CREATE INDEX glass_transcript_source_16_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_16" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_16_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_16" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_17" (
    CHECK ( chromosome_id = 17 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_17_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_17" USING btree (id);
CREATE INDEX glass_transcript_source_17_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_17" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_17_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_17" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_18" (
    CHECK ( chromosome_id = 18 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_18_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_18" USING btree (id);
CREATE INDEX glass_transcript_source_18_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_18" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_18_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_18" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_19" (
    CHECK ( chromosome_id = 19 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_19_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_19" USING btree (id);
CREATE INDEX glass_transcript_source_19_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_19" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_19_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_19" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_20" (
    CHECK ( chromosome_id = 20 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_20_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_20" USING btree (id);
CREATE INDEX glass_transcript_source_20_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_20" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_20_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_20" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_21" (
    CHECK ( chromosome_id = 21 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_21_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_21" USING btree (id);
CREATE INDEX glass_transcript_source_21_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_21" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_21_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_21" USING btree (sequencing_run_id);


CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_source_22" (
    CHECK ( chromosome_id = 22 )
) INHERITS ("glass_atlas_%s_%s_prep"."glass_transcript_source");
CREATE INDEX glass_transcript_source_22_pkey_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_22" USING btree (id);
CREATE INDEX glass_transcript_source_22_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_22" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_source_22_sequencing_run_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_source_22" USING btree (sequencing_run_id);


CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_prep.glass_transcript_source_insert_trigger()
RETURNS TRIGGER AS $$
BEGIN
    EXECUTE 'INSERT INTO glass_atlas_%s_%s_prep.glass_transcript_source_' || NEW.chromosome_id || ' VALUES ('
    || quote_literal(NEW.id) || ','
    || quote_literal(NEW.chromosome_id) || ','
    || quote_literal(NEW.glass_transcript_id) || ','
    || quote_literal(NEW.sequencing_run_id) || ','
    || quote_literal(NEW.tag_count) || ','
    || quote_literal(NEW.gaps) || ','
    || quote_literal(NEW.polya_count)
    || ')'
    ;
    RETURN NULL;
END;
$$
LANGUAGE 'plpgsql';

-- Trigger function for inserts on main table
CREATE TRIGGER glass_transcript_source_trigger
    BEFORE INSERT ON "glass_atlas_%s_%s_prep"."glass_transcript_source"
    FOR EACH ROW EXECUTE PROCEDURE glass_atlas_%s_%s_prep.glass_transcript_source_insert_trigger();





CREATE TABLE "glass_atlas_%s_%s_prep"."glass_transcript_label" (
    "id" int4 NOT NULL,
    "glass_transcript_id" int4 DEFAULT NULL,
    "transcript_class_id" int4 DEFAULT NULL,
    "chromosome_id" int4 DEFAULT NULL,
    "strand" int2 DEFAULT NULL,
    "start_end" box DEFAULT NULL,
    "manual" boolean DEFAULT false,
    "probability" float4 DEFAULT NULL,
    "modified" timestamp(6) NULL DEFAULT NULL,
    "created" timestamp(6) NULL DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s_prep"."glass_transcript_label" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s_prep"."glass_transcript_label_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s_prep"."glass_transcript_label_id_seq" OWNED BY "glass_atlas_%s_%s_prep"."glass_transcript_label".id;
ALTER TABLE "glass_atlas_%s_%s_prep"."glass_transcript_label" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s_prep"."glass_transcript_label_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s_prep"."glass_transcript_label" ADD CONSTRAINT glass_transcript_label_pkey PRIMARY KEY (id);

CREATE INDEX glass_transcript_label_glass_transcript_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_label" USING btree (glass_transcript_id);
CREATE INDEX glass_transcript_label_transcript_class_id_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_label" USING btree (transcript_class_id);
CREATE INDEX glass_transcript_label_manual_idx ON "glass_atlas_%s_%s_prep"."glass_transcript_label" USING btree (manual);

""" % tuple([genome, cell_type]*322)

if __name__ == '__main__':
    print sql(genome, cell_type)