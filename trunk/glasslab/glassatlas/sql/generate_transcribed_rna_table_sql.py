'''
Created on Nov 12, 2010

@author: karmel

** DEPRECATED **

'''

genome = 'mm9'
cell_type = 'thiomac'
def sql(genome, cell_type):
    return """
CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna" (
    "id" int4 NOT NULL,
    "glass_transcript_id" int4 DEFAULT NULL,
    "chromosome_id" int4 DEFAULT NULL,
    "strand" int2 DEFAULT NULL,
    "transcription_start" int8 DEFAULT NULL,
    "transcription_end" int8 DEFAULT NULL,
    "start_end" box DEFAULT NULL,
    "score" numeric DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_id_seq" OWNED BY "glass_atlas_%s_%s_rna"."glass_transcribed_rna".id;
ALTER TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s_rna"."glass_transcribed_rna_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s_rna"."glass_transcribed_rna" ADD CONSTRAINT glass_transcribed_rna_pkey PRIMARY KEY (id);

-- Tables for each chromosome
CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_1" (
    CHECK ( chromosome_id = 1 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_1_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_1" USING btree (id);
CREATE INDEX glass_transcribed_rna_1_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_1" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_1_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_1" USING btree (strand);
CREATE INDEX glass_transcribed_rna_1_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_1" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_1_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_1" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_2" (
    CHECK ( chromosome_id = 2 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_2_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_2" USING btree (id);
CREATE INDEX glass_transcribed_rna_2_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_2" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_2_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_2" USING btree (strand);
CREATE INDEX glass_transcribed_rna_2_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_2" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_2_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_2" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_3" (
    CHECK ( chromosome_id = 3 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_3_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_3" USING btree (id);
CREATE INDEX glass_transcribed_rna_3_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_3" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_3_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_3" USING btree (strand);
CREATE INDEX glass_transcribed_rna_3_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_3" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_3_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_3" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_4" (
    CHECK ( chromosome_id = 4 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_4_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_4" USING btree (id);
CREATE INDEX glass_transcribed_rna_4_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_4" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_4_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_4" USING btree (strand);
CREATE INDEX glass_transcribed_rna_4_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_4" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_4_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_4" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_5" (
    CHECK ( chromosome_id = 5 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_5_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_5" USING btree (id);
CREATE INDEX glass_transcribed_rna_5_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_5" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_5_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_5" USING btree (strand);
CREATE INDEX glass_transcribed_rna_5_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_5" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_5_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_5" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_6" (
    CHECK ( chromosome_id = 6 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_6_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_6" USING btree (id);
CREATE INDEX glass_transcribed_rna_6_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_6" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_6_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_6" USING btree (strand);
CREATE INDEX glass_transcribed_rna_6_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_6" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_6_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_6" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_7" (
    CHECK ( chromosome_id = 7 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_7_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_7" USING btree (id);
CREATE INDEX glass_transcribed_rna_7_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_7" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_7_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_7" USING btree (strand);
CREATE INDEX glass_transcribed_rna_7_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_7" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_7_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_7" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_8" (
    CHECK ( chromosome_id = 8 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_8_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_8" USING btree (id);
CREATE INDEX glass_transcribed_rna_8_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_8" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_8_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_8" USING btree (strand);
CREATE INDEX glass_transcribed_rna_8_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_8" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_8_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_8" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_9" (
    CHECK ( chromosome_id = 9 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_9_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_9" USING btree (id);
CREATE INDEX glass_transcribed_rna_9_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_9" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_9_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_9" USING btree (strand);
CREATE INDEX glass_transcribed_rna_9_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_9" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_9_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_9" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_10" (
    CHECK ( chromosome_id = 10 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_10_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_10" USING btree (id);
CREATE INDEX glass_transcribed_rna_10_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_10" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_10_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_10" USING btree (strand);
CREATE INDEX glass_transcribed_rna_10_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_10" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_10_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_10" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_11" (
    CHECK ( chromosome_id = 11 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_11_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_11" USING btree (id);
CREATE INDEX glass_transcribed_rna_11_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_11" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_11_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_11" USING btree (strand);
CREATE INDEX glass_transcribed_rna_11_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_11" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_11_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_11" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_12" (
    CHECK ( chromosome_id = 12 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_12_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_12" USING btree (id);
CREATE INDEX glass_transcribed_rna_12_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_12" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_12_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_12" USING btree (strand);
CREATE INDEX glass_transcribed_rna_12_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_12" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_12_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_12" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_13" (
    CHECK ( chromosome_id = 13 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_13_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_13" USING btree (id);
CREATE INDEX glass_transcribed_rna_13_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_13" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_13_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_13" USING btree (strand);
CREATE INDEX glass_transcribed_rna_13_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_13" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_13_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_13" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_14" (
    CHECK ( chromosome_id = 14 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_14_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_14" USING btree (id);
CREATE INDEX glass_transcribed_rna_14_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_14" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_14_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_14" USING btree (strand);
CREATE INDEX glass_transcribed_rna_14_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_14" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_14_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_14" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_15" (
    CHECK ( chromosome_id = 15 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_15_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_15" USING btree (id);
CREATE INDEX glass_transcribed_rna_15_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_15" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_15_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_15" USING btree (strand);
CREATE INDEX glass_transcribed_rna_15_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_15" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_15_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_15" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_16" (
    CHECK ( chromosome_id = 16 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_16_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_16" USING btree (id);
CREATE INDEX glass_transcribed_rna_16_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_16" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_16_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_16" USING btree (strand);
CREATE INDEX glass_transcribed_rna_16_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_16" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_16_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_16" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_17" (
    CHECK ( chromosome_id = 17 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_17_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_17" USING btree (id);
CREATE INDEX glass_transcribed_rna_17_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_17" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_17_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_17" USING btree (strand);
CREATE INDEX glass_transcribed_rna_17_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_17" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_17_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_17" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_18" (
    CHECK ( chromosome_id = 18 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_18_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_18" USING btree (id);
CREATE INDEX glass_transcribed_rna_18_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_18" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_18_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_18" USING btree (strand);
CREATE INDEX glass_transcribed_rna_18_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_18" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_18_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_18" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_19" (
    CHECK ( chromosome_id = 19 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_19_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_19" USING btree (id);
CREATE INDEX glass_transcribed_rna_19_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_19" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_19_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_19" USING btree (strand);
CREATE INDEX glass_transcribed_rna_19_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_19" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_19_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_19" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_20" (
    CHECK ( chromosome_id = 20 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_20_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_20" USING btree (id);
CREATE INDEX glass_transcribed_rna_20_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_20" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_20_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_20" USING btree (strand);
CREATE INDEX glass_transcribed_rna_20_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_20" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_20_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_20" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_21" (
    CHECK ( chromosome_id = 21 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_21_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_21" USING btree (id);
CREATE INDEX glass_transcribed_rna_21_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_21" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_21_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_21" USING btree (strand);
CREATE INDEX glass_transcribed_rna_21_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_21" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_21_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_21" USING btree (glass_transcript_id);

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_22" (
    CHECK ( chromosome_id = 22 )
) INHERITS ("glass_atlas_%s_%s_rna"."glass_transcribed_rna");
CREATE INDEX glass_transcribed_rna_22_pkey_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_22" USING btree (id);
CREATE INDEX glass_transcribed_rna_22_chr_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_22" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_22_strand_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_22" USING btree (strand);
CREATE INDEX glass_transcribed_rna_22_start_end_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_22" USING gist (start_end);
CREATE INDEX glass_transcribed_rna_22_glass_transcript_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_22" USING btree (glass_transcript_id);

CREATE OR REPLACE FUNCTION glass_atlas_%s_%s_rna.glass_transcribed_rna_insert_trigger()
RETURNS TRIGGER AS $$
BEGIN
    EXECUTE 'INSERT INTO glass_atlas_%s_%s_rna.glass_transcribed_rna_' || NEW.chromosome_id || ' VALUES ('
    || quote_literal(NEW.id) || ','
    || quote_literal(NEW.glass_transcript_id) || ','
    || quote_literal(NEW.chromosome_id) || ','
    || quote_literal(NEW.strand) || ','
    || quote_literal(NEW.transcription_start) || ','
    || quote_literal(NEW.transcription_end) || ','
    || 'public.make_box(' || quote_literal(NEW.transcription_start) || ', 0, ' 
        || quote_literal(NEW.transcription_end) || ', 0)'
    || ')';
    RETURN NULL;
END;
$$
LANGUAGE 'plpgsql';

-- Trigger function for inserts on main table
CREATE TRIGGER glass_transcribed_rna_trigger
    BEFORE INSERT ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna"
    FOR EACH ROW EXECUTE PROCEDURE glass_atlas_%s_%s_rna.glass_transcribed_rna_insert_trigger();

CREATE TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source" (
    "id" int4 NOT NULL,
    "glass_transcribed_rna_id" int4 DEFAULT NULL,
    "sequencing_run_id" int4 DEFAULT NULL,
    "tag_count" int4 DEFAULT NULL,
    "gaps" int4 DEFAULT NULL,
    "polya_count" int4 DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source_id_seq" OWNED BY "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source".id;
ALTER TABLE "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s_rna"."glass_transcribed_rna_source_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source" ADD CONSTRAINT glass_transcribed_rna_source_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcribed_rna_source_transcribed_rna_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source" USING btree (glass_transcribed_rna_id);
CREATE INDEX glass_transcribed_rna_source_sequencing_run_idx ON "glass_atlas_%s_%s_rna"."glass_transcribed_rna_source" USING btree (sequencing_run_id);


""" % tuple([genome, cell_type]*176)

if __name__ == '__main__':
    print sql(genome, cell_type)