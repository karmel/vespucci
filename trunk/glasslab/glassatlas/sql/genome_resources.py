'''
Created on Nov 12, 2012

@author: karmel
'''

from glasslab.config import current_settings
from glasslab.utils.database import SqlGenerator

class GenomeResourcesSqlGenerator(SqlGenerator):
    ''' Generates the SQL queries for building DB schema. '''
    genome = None

    def __init__(self, genome=None, cell_type=None, staging=None, user=None):
        self.genome = genome or current_settings.GENOME.lower()
        self.staging = staging or current_settings.STAGING
        
        self.schema_name = 'genome_resources_{0}'.format(self.genome)
        super(GenomeResourcesSqlGenerator, self).__init__()

    def all_sql(self):
        s = self.schema()
        s += self.chromosome()
        s += self.sequence_identifier()
        s += self.sequence_transcription_region()
        s += self.sequencing_run()
        
        return s
    
    def fill_tables_mm9(self):
        s = self.insert_chromosome_mm9_values()
        s += self.import_ucsc_sequence_mm9_values()
        s += self.insert_sequence_mm9_values()
        s += self.insert_sequence_transcription_region_mm9_values()
        
        return s
    
    def schema(self):
        return """
        CREATE SCHEMA "{schema_name}" AUTHORIZATION "{user}";
        """.format(schema_name_prefix=self.schema_name_prefix, user=self.user)

    def chromosome(self):
        table_name = 'chromosome'
        return """
        CREATE TABLE "{schema_name}"."{table_name}" (
            "id" int4 NOT NULL,
            "name" varchar(25),
            "length" bigint
        );
        """.format(schema_name=self.schema_name, table_name=table_name)\
        + self.pkey_sequence_sql(self.schema_name, table_name)
        
    def insert_chromosome_mm9_values(self):
        return """
        INSERT INTO chromosome (name, length) values ('chr1', 197195433), ('chr2', 181748088), 
            ('chr3', 159599784), ('chr4', 155630121), ('chr5', 152537260), ('chr6', 149517038), 
            ('chr7', 152524554), ('chr8', 131738872), ('chr9', 124076173), ('chrX', 166650297), 
            ('chrY', 15902556), ('chr10', 129993256), ('chr11', 121843857), ('chr12', 121257531), 
            ('chr13', 120284313), ('chr14', 125194865), ('chr15', 103494975), ('chr16', 98319151), 
            ('chr17', 95272652), ('chr18', 90772032), ('chr19', 61342431), ('chrM', 16300);
        """
    
    def sequence_identifier(self):
        table_name = 'sequence_identifier'
        return """
        CREATE TYPE "{schema_name}"."{table_name}_type" AS ENUM('mRNA','RNA');

        CREATE TABLE "{schema_name}"."{table_name}" (
            "id" integer NOT NULL,
            "sequence_identifier" varchar(50),
            "type" sequence_identifier_type DEFAULT NULL
        );
        ALTER TABLE ONLY "{schema_name}"."{table_name}" ADD CONSTRAINT {table_name}_sequence_identifier_key UNIQUE (sequence_identifier);
        """.format(schema_name=self.schema_name, table_name=table_name)\
        + self.pkey_sequence_sql(self.schema_name, table_name)
        
    def sequence_transcription_region(self):
        table_name = 'sequence_transcription_region'
        return """
        CREATE TABLE "{schema_name}"."{table_name}" (
            id integer NOT NULL,
            sequence_identifier_id integer,
            chromosome_id integer,
            strand smallint,
            transcription_start bigint,
            transcription_end bigint,
            start_end box,
            start_site_1000 box,
            start_end_1000 box
        );
        CREATE INDEX {table_name}_chr_idx ON "{schema_name}"."{table_name}" USING btree (chromosome_id);
        CREATE INDEX {table_name}_strand_idx ON "{schema_name}"."{table_name}" USING btree (strand);
        CREATE INDEX {table_name}_start_end_idx ON "{schema_name}"."{table_name}" USING gist (start_end);
        CREATE INDEX {table_name}_start_end_1000_idx ON "{schema_name}"."{table_name}" USING gist (start_end_1000);
        """.format(schema_name=self.schema_name, table_name=table_name)\
        + self.pkey_sequence_sql(self.schema_name, table_name)
        
    def import_ucsc_sequence_mm9_values(self):
        '''
        Create a temp table to be normalized and associated appropriately.
        
        File downloaded at: http://hgdownload.soe.ucsc.edu/goldenPath/mm9/database/refGene.txt.gz
        
        This is hardcoded to work with the UCSC download as it is. 
        More flexible import logic can be created here.
        '''
        path_to_file = '~/Downloads/refGene.txt'
        f = open(path_to_file)
        output = []
        for l in f:
            fields = l.split('\t')
            output.append("""
                INSERT into "{schema_name}"."refGene" 
                    ("name","chrom","strand","txStart","txEnd") 
                    VALUES ({0}, {1}, {2}, {3}, {4});
                """.format(fields[1], fields[2], fields[3], fields[4], fields[5],
                           schema_name=self.schema_name))
        
        return """
        CREATE TABLE "{schema_name}"."refGene" (
            "name" varchar(50) NOT NULL DEFAULT NULL,
            "chrom" varchar(25) NOT NULL DEFAULT NULL,
            "strand" varchar(1) NOT NULL DEFAULT NULL,
            "txStart" int8 NOT NULL DEFAULT NULL,
            "txEnd" int8 NOT NULL DEFAULT NULL
        );
        """.format(schema_name=self.schema_name) \
        + '\n'.join(output)
    
    def insert_sequence_mm9_values(self):
        table_name = 'sequence_identifier'
        return """
        INSERT INTO "{schema_name}"."{table_name}" ("sequence_identifier", "type") 
            SELECT DISTINCT "name", 
            (CASE WHEN substring("name" from 1 for 2) = 'NM' THEN sequence_identifier_type('mRNA')
            WHEN  substring("name" from 1 for 2) = 'NR' THEN sequence_identifier_type('RNA')
            ELSE NULL END)
         from "{schema_name}"."refGene";
        """.format(schema_name=self.schema_name, table_name=table_name)
    
    def insert_sequence_transcription_region_mm9_values(self):
        table_name = 'sequence_transcription_region'
        return """
        INSERT INTO "{schema_name}"."{table_name}" 
        (sequence_identifier_id, chromosome_id, strand, transcription_start, transcription_end)
        SELECT 
        seq.id, 
        chr.id,
        (CASE WHEN ref.strand = '-' THEN 1
        ELSE 0 END),
        ref."txStart", ref."txEnd"
        FROM "{schema_name}"."sequence_identifier" seq, "{schema_name}"."refGene" ref, 
            "{schema_name}"."chromosome" chr
        WHERE 
        ref."name" = seq.sequence_identifier
        AND ref."chrom" = chr."name";
        
        UPDATE "{schema_name}"."{table_name}"  
        SET start_end = public.make_box(("transcription_start"),0,"transcription_end",0),
        start_site_1000 = public.make_box(("transcription_start" - 1000),0,("transcription_start" + 1000),0),
        start_end_1000 = public.make_box(("transcription_start" - 1000),0,("transcription_end" + 1000),0)
         WHERE strand = 0;
        
        UPDATE "{schema_name}"."{table_name}"  
        SET start_end = public.make_box("transcription_start"::float,("transcription_end")::float),
        start_site_1000 = public.make_box(("transcription_end" - 1000),0,("transcription_end" + 1000),0),
        start_end_1000 = public.make_box(("transcription_start" - 1000),0,("transcription_end" + 1000),0)
        WHERE strand = 1;
        """.format(schema_name=self.schema_name, table_name=table_name)

    
    def sequencing_run(self):
        table_name = 'sequencing_run'
        return """
        CREATE TABLE "{schema_name}"."{table_name}" (
            "id" int4 NOT NULL,
            "cell_type" varchar(50) DEFAULT NULL,
            "name" varchar(100) DEFAULT NULL,
            "source_table" varchar(100) DEFAULT NULL,
            "total_tags" int8 DEFAULT NULL,
            "modified" timestamp(6) NULL DEFAULT NULL,
            "created" timestamp(6) NULL DEFAULT NULL
        );
        CREATE UNIQUE INDEX {table_name}_source_table_idx ON "{schema_name}"."{table_name}" USING btree (source_table);
        """.format(self.genome, user=self.user) \
        + self.pkey_sequence_sql(schema_name=self.schema_name, table_name=table_name)
