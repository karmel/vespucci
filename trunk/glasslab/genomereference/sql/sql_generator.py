'''
Created on Oct 9, 2012

@author: karmel

'''
from glasslab.config import current_settings
from glasslab.utils.database import SqlGenerator

class GenomeReferenceSqlGenerator(SqlGenerator):
    ''' Generates the SQL queries for building DB schema. '''
    genome = None
    schema_name = None
    
    def __init__(self, genome=None, user=None):
        self.genome = genome or current_settings.GENOME.lower()
        self.schema_name = 'genome_reference_{0}'.format(self.genome)
        
        super(GenomeReferenceSqlGenerator, self).__init__()
    
    def schema(self, suffix=''):
        return """
        CREATE SCHEMA "genome_reference_{0}" AUTHORIZATION "{user}";
        """.format(self.genome, user=self.user)
        
    def chromosome_table(self):
        table_name = 'chromosome'
        return """
        CREATE TABLE "{0}"."{1}" (
            "id" int4 NOT NULL,
            "name" varchar(25) DEFAULT NULL,
            "length" int8 DEFAULT NULL
        );
        CREATE INDEX "{1}_name_idx" ON "{0}"."{1}" USING btree(name);
        """.format(self.schema_name, table_name) \
        + self.pkey_sequence_sql(self.schema_name, table_name)
    
    def sequence_identifier(self):
        '''
        RefSeq ID table.
        '''
        table_name = 'sequence_identifier'
        return """
        CREATE TYPE "{0}"."{1}_type" AS ENUM ('mRNA', 'RNA');
        CREATE TABLE "{0}"."{1}" (
            "id" int4 NOT NULL,
            "sequence_identifier" varchar(50) DEFAULT NULL,
            "type" "{0}"."{1}_type" DEFAULT NULL
            CONSTRAINT "{1}_sequence_identifier_key" UNIQUE ("sequence_identifier")
        );""".format(self.schema_name, table_name) \
        + self.pkey_sequence_sql(self.schema_name, table_name)
        
    def sequence_detail(self):
        '''
        Details about RefSeq IDs that are useful for human reference.
        '''
        table_name = 'sequence_detail'
        return """
        CREATE TABLE "{0}"."{1}" (
            "id" int4 NOT NULL,
            "sequence_identifier_id" int4 DEFAULT NULL,
            "gene_name" varchar(100) DEFAULT NULL::bpchar,
            "ensembl_id" varchar(100) DEFAULT NULL::bpchar,
            "pfam_id" varchar(100) DEFAULT NULL::bpchar,
            "description" varchar(255) DEFAULT NULL::bpchar
        );
        CREATE UNIQUE INDEX "{1}_sequence_identifier_idx" ON "{0}"."{1}" USING btree(sequence_identifier_id);

        );""".format(self.schema_name, table_name) \
        + self.pkey_sequence_sql(self.schema_name, table_name)
        
        
    def sequence_transcription_region(self):
        '''
        RefSeq genomic locations.
        '''
        return self.transcription_region('sequence', 'sequence_identifier')

    def non_coding_rna(self):
        '''
        Assorted ncRNA, normalized
        '''
        table_name = 'non_coding_rna'
        return """
        CREATE TABLE "{0}"."{1}" (
            "id" int4 NOT NULL,
            "type" varchar(100) DEFAULT NULL,
            "description" varchar(255) DEFAULT NULL,
            "source" varchar(255) DEFAULT NULL
        );
        CREATE UNIQUE INDEX "non_coding_rna_type_name_idx" ON "{0}"."{1}" USING btree(type, description);
        );""".format(self.schema_name, table_name) \
        + self.pkey_sequence_sql(self.schema_name, table_name)
        
    def non_coding_transcription_region(self):
        '''
        Genomic locations for ncRNA.
        '''
        return self.transcription_region('non_coding', 'non_coding_rna')
    
    def transcription_region(self, region_type, object_relation):
        table_name = '{0}_transcription_region'.format(region_type)
        return """
        CREATE TABLE "{0}"."{1}" (
            "id" int4 NOT NULL,
            "{2}_id" int4 DEFAULT NULL,
            "chromosome_id" int4 DEFAULT NULL,
            "strand" int2 DEFAULT NULL,
            "transcription_start" int8 DEFAULT NULL,
            "transcription_end" int8 DEFAULT NULL,
            "start_end" box DEFAULT NULL
        );
        CREATE INDEX "{1}_chr_idx" ON "genome_reference_mm9"."{1}" USING btree(chromosome_id);
        CREATE INDEX "{1}_start_end_idx" ON "genome_reference_mm9"."{1}" USING gist(start_end);
        CREATE INDEX "{1}_strand_idx" ON "genome_reference_mm9"."{1}" USING btree(strand);
        """.format(self.schema_name, table_name, object_relation) \
        + self.pkey_sequence_sql(self.schema_name, table_name)
        
        
        
    def sequencing_run_table(self):
        table_name = 'sequencing_run'
        return """
        CREATE TABLE "{0}"."{table_name}" (
            "id" int4 NOT NULL,
            "source_table" varchar(100) DEFAULT NULL
        );
        CREATE UNIQUE INDEX sequencing_run_source_table_idx ON "{0}"."{table_name}" USING btree (source_table);
        
        """.format(self.schema_name, table_name=table_name) \
        + self.pkey_sequence_sql(self.schema_name, table_name)
    
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