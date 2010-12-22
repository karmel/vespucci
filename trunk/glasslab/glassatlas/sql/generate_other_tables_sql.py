'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcript tables.
'''

genome = 'mm11'
cell_type='thiomac'
sql = """
CREATE TYPE "glass_atlas_%s_%s"."sequencing_run_type" AS ENUM('Gro-Seq','RNA-Seq','ChIP-Seq');
CREATE TABLE "glass_atlas_%s_%s"."sequencing_run" (
    "id" int4 NOT NULL,
    "type" glass_atlas_%s_%s.sequencing_run_type DEFAULT NULL,
    "cell_type" character(50) DEFAULT NULL,
    "name" character(100) DEFAULT NULL,
    "source_table" character(100) DEFAULT NULL,
    "description" character(255) DEFAULT NULL,
    "total_tags" int8 DEFAULT NULL,
    "percent_mapped" numeric(5,2) DEFAULT NULL,
    "modified" timestamp(6) NULL DEFAULT NULL,
    "created" timestamp(6) NULL DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s"."sequencing_run" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s"."sequencing_run_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s"."sequencing_run_id_seq" OWNED BY "glass_atlas_%s_%s"."sequencing_run".id;
ALTER TABLE "glass_atlas_%s_%s"."sequencing_run" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s"."sequencing_run_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s"."sequencing_run" ADD CONSTRAINT sequencing_run_pkey PRIMARY KEY (id);
CREATE UNIQUE INDEX sequencing_run_source_table_idx ON "glass_atlas_%s_%s"."sequencing_run" USING btree (source_table);
""" % tuple([genome, cell_type]*11)
print sql