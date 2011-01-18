'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcript tables.
'''

genome = 'mm9'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
CREATE TYPE "glass_atlas_%s"."sequencing_run_type" AS ENUM('Gro-Seq','RNA-Seq','ChIP-Seq');
CREATE TABLE "glass_atlas_%s"."sequencing_run" (
    "id" int4 NOT NULL,
    "type" glass_atlas_%s.sequencing_run_type DEFAULT NULL,
    "cell_type" character(50) DEFAULT NULL,
    "name" character(100) DEFAULT NULL,
    "source_table" character(100) DEFAULT NULL,
    "description" character(255) DEFAULT NULL,
    "total_tags" int8 DEFAULT NULL,
    "percent_mapped" numeric(5,2) DEFAULT NULL,
    "peak_type_id" int4 DEFAULT NULL,
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

CREATE TABLE "glass_atlas_%s"."sequencing_run_annotation" (
    "id" int4 NOT NULL,
    "sequencing_run_id" int4 DEFAULT NULL,
    "note" character(100) DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s"."sequencing_run_annotation" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."sequencing_run_annotation_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."sequencing_run_annotation_id_seq" OWNED BY "glass_atlas_%s"."sequencing_run_annotation".id;
ALTER TABLE "glass_atlas_%s"."sequencing_run_annotation" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."sequencing_run_annotation_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."sequencing_run_annotation" ADD CONSTRAINT sequencing_run_annotation_pkey PRIMARY KEY (id);
CREATE INDEX sequencing_run_annotation_run_idx ON "glass_atlas_%s"."sequencing_run_annotation" USING btree (sequencing_run_id);

CREATE TABLE "glass_atlas_%s"."peak_type" (
    "id" int4 NOT NULL,
    "type" character(50) DEFAULT NULL,
    "diffuse" boolean DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s"."peak_type" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s"."peak_type_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s"."peak_type_id_seq" OWNED BY "glass_atlas_%s"."peak_type".id;
ALTER TABLE "glass_atlas_%s"."peak_type" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s"."peak_type_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s"."peak_type" ADD CONSTRAINT peak_type_pkey PRIMARY KEY (id);
""" % tuple([genome]*28)

if __name__ == '__main__':
    print sql(genome, cell_type)