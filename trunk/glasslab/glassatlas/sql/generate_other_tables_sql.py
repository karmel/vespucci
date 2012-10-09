'''
Created on Nov 12, 2010

@author: karmel

Create table statements for miscellaneous tables.
'''
from glasslab.config import current_settings

genome = 'mm9'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
CREATE TYPE "glass_atlas_{0}"."sequencing_run_type" AS ENUM('Gro-Seq','RNA-Seq','ChIP-Seq');
CREATE TABLE "glass_atlas_{0}"."sequencing_run" (
    "id" int4 NOT NULL,
    "type" glass_atlas_{0}.sequencing_run_type DEFAULT NULL,
    "cell_type" varchar(50) DEFAULT NULL,
    "name" varchar(100) DEFAULT NULL,
    "source_table" varchar(100) DEFAULT NULL,
    "description" varchar(255) DEFAULT NULL,
    "total_tags" int8 DEFAULT NULL,
    "percent_mapped" numeric(5,2) DEFAULT NULL,
    "peak_type_id" int4 DEFAULT NULL,
    "standard" boolean DEFAULT false,
    "requires_reload" boolean DEFAULT false,
    "modified" timestamp(6) NULL DEFAULT NULL,
    "created" timestamp(6) NULL DEFAULT NULL
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

""".format(genome,
           user=current_settings.DATABASES['default']['USER'])
