'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcript tables.
'''

genome = 'gap2_200'
cell_type = 'thiomac'
def sql(genome, cell_type):
    return """
CREATE TABLE "glass_atlas_%s_%s"."glass_transcribed_rna" (
    "id" int4 NOT NULL,
    "glass_transcript_id" int4 DEFAULT NULL,
    "chromosome_id" int4 DEFAULT NULL,
    "strand" int2 DEFAULT NULL,
    "transcription_start" int8 DEFAULT NULL,
    "transcription_end" int8 DEFAULT NULL,
    "start_end" "public"."cube" DEFAULT NULL,
    "modified" timestamp(6) NULL DEFAULT NULL,
    "created" timestamp(6) NULL DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s"."glass_transcribed_rna" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s"."glass_transcribed_rna_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s"."glass_transcribed_rna_id_seq" OWNED BY "glass_atlas_%s_%s"."glass_transcribed_rna".id;
ALTER TABLE "glass_atlas_%s_%s"."glass_transcribed_rna" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s"."glass_transcribed_rna_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s"."glass_transcribed_rna" ADD CONSTRAINT glass_transcribed_rna_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcribed_rna_glass_transcript_idx ON "glass_atlas_%s_%s"."glass_transcribed_rna" USING btree (glass_transcript_id);
CREATE INDEX glass_transcribed_rna_chr_idx ON "glass_atlas_%s_%s"."glass_transcribed_rna" USING btree (chromosome_id);
CREATE INDEX glass_transcribed_rna_strand_idx ON "glass_atlas_%s_%s"."glass_transcribed_rna" USING btree (strand);
CREATE INDEX glass_transcribed_rna_start_end_idx ON "glass_atlas_%s_%s"."glass_transcribed_rna" USING gist (start_end);

CREATE TABLE "glass_atlas_%s_%s"."glass_transcribed_rna_source" (
    "id" int4 NOT NULL,
    "glass_transcribed_rna_id" int4 DEFAULT NULL,
    "sequencing_run_id" int4 DEFAULT NULL,
    "tag_count" int4 DEFAULT NULL,
    "gaps" int4 DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s"."glass_transcribed_rna_source" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s"."glass_transcribed_rna_source_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s"."glass_transcribed_rna_source_id_seq" OWNED BY "glass_atlas_%s_%s"."glass_transcribed_rna_source".id;
ALTER TABLE "glass_atlas_%s_%s"."glass_transcribed_rna_source" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s"."glass_transcribed_rna_source_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s"."glass_transcribed_rna_source" ADD CONSTRAINT glass_transcribed_rna_source_pkey PRIMARY KEY (id);
CREATE INDEX glass_transcribed_rna_source_transcript_idx ON "glass_atlas_%s_%s"."glass_transcribed_rna_source" USING btree (glass_transcribed_rna_id);

""" % tuple([genome, cell_type]*21)

if __name__ == '__main__':
    print sql(genome, cell_type)