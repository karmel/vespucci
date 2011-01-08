'''
Created on Sep 27, 2010

@author: karmel
'''
from django.db import models
from glasslab.utils.datatypes.genome_reference import Chromosome
from glasslab.utils.datatypes.basic_model import DynamicTable, CubeField
from glasslab.utils.database import execute_query
        
class GlassPeak(DynamicTable):
    '''
    From MACS::
        
        chr     start   end     length  summit  tags    -10*log10(pvalue)       fold_enrichment
    '''
    
    chromosome      = models.ForeignKey(Chromosome)
    strand          = models.IntegerField(max_length=1)
    start           = models.IntegerField(max_length=12)
    end             = models.IntegerField(max_length=12)
    
    start_end       = CubeField(max_length=255, help_text='This is a placeholder for the PostgreSQL cube type.') 
    
    diffuse         = models.BooleanField(default=False, help_text='Is this a diffuse region, rather than focal peak?')
    length          = models.IntegerField(max_length=12)
    summit          = models.IntegerField(max_length=12)
    tag_count       = models.IntegerField(max_length=12)
    log_ten_p_value = models.DecimalField(max_digits=10, decimal_places=4)
    fold_enrichment = models.DecimalField(max_digits=10, decimal_places=4)
    
    
    @classmethod        
    def create_table(cls, name):
        '''
        Create table that will be used for these peaks,
        dynamically named.
        '''
        cls.set_table_name('peak_' + name)
        
        table_sql = """
        CREATE TABLE "%s" (
            id serial4,
            chromosome_id int4,
            "start" int8,
            "end" int8,
            start_end public.cube,
            diffuse boolean default false,
            "length" int4,
            summit int8,
            tag_count int4,
            log_ten_p_value decimal(10,6),
            fold_enrichment decimal(10,6)
            );
        CREATE SEQUENCE "%s_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "%s_id_seq" OWNED BY "%s".id;
        ALTER TABLE "%s" ALTER COLUMN id SET DEFAULT nextval('"%s_id_seq"'::regclass);
        ALTER TABLE ONLY "%s" ADD CONSTRAINT %s_pkey PRIMARY KEY (id);
        """ % (cls._meta.db_table, 
               cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, cls._meta.db_table,
               cls._meta.db_table, cls.name)
        execute_query(table_sql)
        
        cls.table_created = True
    
    @classmethod
    def add_indices(cls):
        update_query = """
        CREATE INDEX %s_chr_idx ON "%s" USING btree (chromosome_id);
        CREATE INDEX %s_strand_idx ON "%s" USING btree (strand);
        CREATE INDEX %s_start_end_idx ON "%s" USING gist (start_end);
        """ % (cls.name, cls._meta.db_table,
               cls.name, cls._meta.db_table,
               cls.name, cls._meta.db_table,
               cls._meta.db_table)
        execute_query(update_query)
            
    @classmethod
    def init_from_macs_row(cls, row):
        '''
        From a standard tab-delimited MACS peak file, create model instance.
        '''
        return cls(chromosome=Chromosome.objects.get(name=str(row[0]).strip()),
                     start=int(row[1]),
                     end=int(row[2]),
                     length=int(row[3]),
                     summit=int(row[4]),
                     tag_count=int(row[5]),
                     log_ten_p_value=str(row[6]),
                     fold_enrichment=str(row[7]))
    
