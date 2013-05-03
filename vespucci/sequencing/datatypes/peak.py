'''
Created on Sep 27, 2010

@author: karmel
'''
from django.db import models, connection
from vespucci.genomereference.datatypes import Chromosome
from vespucci.utils.datatypes.basic_model import Int8RangeField, DynamicTable
from vespucci.utils.database import execute_query
   
       
class AtlasPeak(DynamicTable):
    '''
    Peaks derived from HOMER, MACS, or Sicer peak-finding software
    can be loaded in to be compared to transcripts.
    '''
    
    chromosome = models.ForeignKey(Chromosome)
    start = models.IntegerField(max_length=12)
    end = models.IntegerField(max_length=12)
    
    start_end = Int8RangeField(max_length=255) 
    
    length = models.IntegerField(max_length=12)
    summit = models.IntegerField(max_length=12)
    tag_count = models.DecimalField(max_digits=8, decimal_places=2, 
                                    null=True, default=None)
    raw_tag_count = models.DecimalField(max_digits=8, decimal_places=2, 
                                        null=True, default=None)
    
    score = models.DecimalField(max_digits=8, decimal_places=2, 
                                null=True, default=None)
    p_value = models.DecimalField(max_digits=6, decimal_places=4, 
                                  null=True, default=None)
    p_value_exp = models.IntegerField(max_length=12, null=True, default=None, 
                            help_text='Exponent of 10 in p_value x 10^y')
    log_ten_p_value = models.DecimalField(max_digits=10, decimal_places=2, 
                                          null=True, default=None)
    fold_enrichment = models.DecimalField(max_digits=10, decimal_places=2, 
                                          null=True, default=None)
    fdr_threshold = models.DecimalField(max_digits=6, decimal_places=4, 
                                        null=True, default=None)
    fdr_threshold_exp = models.IntegerField(max_length=12, null=True, default=None, 
                            help_text='Exponent of 10 in fdr_threshold x 10^y')
    
    
    @classmethod        
    def create_table(cls, name):
        '''
        Create table that will be used for these peaks,
        dynamically named.
        '''
        cls.set_table_name('peak_' + name)
        
        table_sql = """
        CREATE TABLE "%s" (
            id int4,
            chromosome_id int4,
            "start" int8,
            "end" int8,
            start_end int8range,
            "length" int4,
            summit int8,
            tag_count decimal(8,2) default NULL,
            raw_tag_count decimal(8,2) default NULL,
            score decimal(8,2) default NULL,
            p_value decimal(6,4) default NULL,
            p_value_exp int4 default NULL,
            log_ten_p_value decimal(10,2) default NULL,
            fold_enrichment decimal(10,2) default NULL,
            fdr_threshold decimal(6,4) default NULL,
            fdr_threshold_exp int4 default NULL
            );
        CREATE SEQUENCE "%s_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "%s_id_seq" OWNED BY "%s".id;
        ALTER TABLE "%s" ALTER COLUMN id 
            SET DEFAULT nextval('"%s_id_seq"'::regclass);
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
        CREATE INDEX %s_start_end_idx ON "%s" USING gist (start_end);
        """ % (cls.name, cls._meta.db_table,
               cls.name, cls._meta.db_table)
        execute_query(update_query)
            
    @classmethod
    def init_from_macs_row(cls, row):
        '''
        From a standard tab-delimited MACS peak file, create model instance.
        '''
        return cls(chromosome=Chromosome.objects.get(name=str(row[0]).strip()),
                     start=int(row[1]),
                     end=int(row[2]),
                     start_end=(int(row[1]), int(row[2])),
                     length=int(row[3]),
                     summit=int(row[4]),
                     tag_count=str(row[5]),
                     log_ten_p_value=str(row[6]),
                     fold_enrichment=str(row[7])
                     )
    @classmethod
    def init_from_homer_row(cls, row):
        '''
        From a standard tab-delimited Homer peak file, create model instance.
        '''
        connection.close()
        try: p_val = str(row[11]).lower().split('e')
        except IndexError: p_val = None
        return cls(chromosome=Chromosome.objects.get(name=str(row[1]).strip()),
                     start=int(row[2]),
                     end=int(row[3]),
                     start_end=(int(row[2]), int(row[3])),
                     length=int(row[3]) - int(row[2]),
                     tag_count=str(row[5]),
                     score=str(row[7]),
                     p_value=p_val and str(p_val[0]) or None,
                     p_value_exp=p_val and len(p_val) > 1 and p_val[1] or 0,
                     fold_enrichment=str(row[10])
                     )
        
    @classmethod
    def init_from_homer_row_old(cls, row):
        '''
        From a standard tab-delimited Homer peak file, create model instance.
        
        For use with older versions of Homer files.
        '''
        connection.close()
        p_val = str(row[12]).lower().split('e')
        return cls(chromosome=Chromosome.objects.get(name=str(row[1]).strip()),
                     start=int(row[2]),
                     end=int(row[3]),
                     start_end=(int(row[2]), int(row[3])),
                     length=int(row[3]) - int(row[2]),
                     tag_count=str(row[5]),
                     raw_tag_count=str(row[9]),
                     score=str(row[8]),
                     p_value=str(p_val[0]),
                     p_value_exp=len(p_val) > 1 and p_val[1] or 0,
                     fold_enrichment=str(row[11])
                     )
        
        
    @classmethod
    def init_from_sicer_row(cls, row):
        '''
        From a standard tab-delimited SICER peak file, create model instance.
        '''
        p_val = str(row[5]).split('e') # '1.34e-12' --> 1.34, -12
        fdr = str(row[7]).split('e')
        return cls(chromosome=Chromosome.objects.get(name=str(row[0]).strip()),
                     start=int(row[1]),
                     end=int(row[2]),
                     start_end=(int(row[1]), int(row[2])),
                     length=int(row[2]) - int(row[1]),
                     tag_count=str(row[3]),
                     p_value=p_val[0],
                     p_value_exp=len(p_val) > 1 and p_val[1] or 0,
                     fold_enrichment=str(row[6]),
                     fdr_threshold=fdr[0],
                     fdr_threshold_exp=len(fdr) > 1 and fdr[1] or 0
                     )
    @classmethod
    def init_from_bed_row(cls, row):
        '''
        From a standard tab-delimited BED peak file, create model instance.
        '''
        return cls(chromosome=Chromosome.objects.get(name=str(row[0]).strip()),
                     start=int(row[1]),
                     end=int(row[2]),
                     start_end=(int(row[1]), int(row[2])),
                     length=int(row[2]) - int(row[1]),
                     score=str(row[4]),
                     )