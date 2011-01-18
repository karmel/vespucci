'''
Created on Nov 12, 2010

@author: karmel

Convenience script for generated create table statements for transcript tables.
'''

genome = 'prep'
cell_type = 'thiomac'
def sql(genome, cell_type):
    return """
CREATE TYPE "glass_atlas_%s_%s"."glass_transcript_feature_relationship" 
    AS ENUM('contains','is contained by','overlaps with','is equal to','is upstream of','is downstream of');
    
CREATE TABLE "glass_atlas_%s_%s"."peak_feature" (
    "id" int4 NOT NULL,
    "glass_transcript_id" int4 DEFAULT NULL,
    "peak_type_id" int4 DEFAULT NULL,
    relationship "glass_atlas_%s_%s"."glass_transcript_feature_relationship"
);
GRANT ALL ON TABLE "glass_atlas_%s_%s"."peak_feature" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s"."peak_feature_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s"."peak_feature_id_seq" OWNED BY "glass_atlas_%s_%s"."peak_feature".id;
ALTER TABLE "glass_atlas_%s_%s"."peak_feature" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s"."peak_feature_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s"."peak_feature" ADD CONSTRAINT peak_feature_pkey PRIMARY KEY (id);
CREATE INDEX peak_feature_glass_transcript_idx ON "glass_atlas_%s_%s"."peak_feature" USING btree (glass_transcript_id);
CREATE INDEX peak_feature_peak_type_idx ON "glass_atlas_%s_%s"."peak_feature" USING btree (peak_type_id);
CREATE INDEX peak_feature_relationship_idx ON "glass_atlas_%s_%s"."peak_feature" USING btree (relationship);

CREATE TABLE "glass_atlas_%s_%s"."peak_feature_instance" (
    "id" int4 NOT NULL,
    "peak_feature_id" int4 DEFAULT NULL,
    "glass_peak_id" int4 DEFAULT NULL,
    "sequencing_run_id" int4 DEFAULT NULL,
    "distance_to_tss" int4 DEFAULT NULL
);
GRANT ALL ON TABLE "glass_atlas_%s_%s"."peak_feature_instance" TO  "glass";
CREATE SEQUENCE "glass_atlas_%s_%s"."peak_feature_instance_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE "glass_atlas_%s_%s"."peak_feature_instance_id_seq" OWNED BY "glass_atlas_%s_%s"."peak_feature_instance".id;
ALTER TABLE "glass_atlas_%s_%s"."peak_feature_instance" ALTER COLUMN id SET DEFAULT nextval('"glass_atlas_%s_%s"."peak_feature_instance_id_seq"'::regclass);
ALTER TABLE ONLY "glass_atlas_%s_%s"."peak_feature_instance" ADD CONSTRAINT peak_feature_instance_pkey PRIMARY KEY (id);
CREATE INDEX peak_feature_instance_peak_feature_idx ON "glass_atlas_%s_%s"."peak_feature_instance" USING btree (peak_feature_id);

""" % tuple([genome, cell_type]*13)

if __name__ == '__main__':
    print sql(genome, cell_type)