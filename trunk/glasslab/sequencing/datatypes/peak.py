'''
Created on Sep 27, 2010

@author: karmel
'''
from django.db import models, connection
from glasslab.utils.datatypes.genome_reference import Chromosome
from glasslab.utils.datatypes.basic_model import DynamicTable, CubeField
from glasslab.utils.database import execute_query
from glasslab.glassatlas.datatypes.metadata import SequencingRun, PeakType
from glasslab.config import current_settings
from multiprocessing import Pool
from glasslab.sequencing.datatypes.tag import GlassSequencingOutput

def multiprocess_glass_peaks(func, cls, *args):
    ''' 
    Convenience method for splitting up queries based on glass peak id.
    '''
    total_count = len(GlassPeak.chromosomes())
    processes = current_settings.ALLOWED_PROCESSES
    p = Pool(processes)
    # Chromosomes are sorted by count descending, so we want to interleave them
    # in order to create even-ish groups.
    chr_lists = [[GlassPeak.chromosomes()[x] for x in xrange(i,total_count,processes)] 
                                for i in xrange(0,processes)]
    
    for chr_list in chr_lists:
        p.apply_async(func, args=[cls, chr_list,] + list(args))
    p.close()
    p.join()    
       
class GlassPeak(GlassSequencingOutput):
    '''
    From MACS::
        
        chr     start   end     length  summit  tags    -10*log10(pvalue)       fold_enrichment
        
    From SICER::
    
        chrom, start, end, ChIP_island_read_count, CONTROL_island_read_count, p_value, fold_change, FDR_threshold
    
    '''
    
    chromosome      = models.ForeignKey(Chromosome)
    start           = models.IntegerField(max_length=12)
    end             = models.IntegerField(max_length=12)
    
    start_end       = CubeField(max_length=255, help_text='This is a placeholder for the PostgreSQL cube type.') 
    
    length          = models.IntegerField(max_length=12)
    summit          = models.IntegerField(max_length=12)
    tag_count       = models.IntegerField(max_length=12)
    
    p_value             = models.DecimalField(max_digits=6, decimal_places=4, null=True, default=None)
    p_value_exp         = models.IntegerField(max_length=12, null=True, default=None, help_text='Exponent of 10 in p_value x 10^y')
    log_ten_p_value     = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    fold_enrichment     = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    fdr_threshold       = models.DecimalField(max_digits=6, decimal_places=4, null=True, default=None)
    fdr_threshold_exp   = models.IntegerField(max_length=12, null=True, default=None, help_text='Exponent of 10 in fdr_threshold x 10^y')
    
    
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
            start_end public.cube,
            "length" int4,
            summit int8,
            tag_count int4,
            p_value decimal(6,4) default NULL,
            p_value_exp int4 default NULL,
            log_ten_p_value decimal(10,4) default NULL,
            fold_enrichment decimal(10,4) default NULL,
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
                     start_end=(int(row[1]),int(row[2]),),
                     length=int(row[3]),
                     summit=int(row[4]),
                     tag_count=int(row[5]),
                     log_ten_p_value=str(row[6]),
                     fold_enrichment=str(row[7])
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
                     start_end=(int(row[1]),int(row[2]),),
                     length=int(row[2]) - int(row[1]),
                     tag_count=int(row[3]),
                     p_value=p_val[0],
                     p_value_exp=len(p_val) > 1 and p_val[1] or 0,
                     fold_enrichment=str(row[6]),
                     fdr_threshold=fdr[0],
                     fdr_threshold_exp=len(fdr) > 1 and fdr[1] or 0
                     )
    
    _peak_type = None
    @classmethod 
    def peak_type(cls, name=None):
        '''
        Try to determine peak type from table name.
        '''
        if cls._peak_type: return cls._peak_type
        name = (name or cls.name).lower()
        peak_types = PeakType.objects.iterator()
        for type in peak_types: 
            if name.find(type.type.strip().lower()) >= 0:
                cls._peak_type = type
                break
        return cls._peak_type
    
    @classmethod 
    def add_record_of_tags(cls, description='', type='ChIP-Seq', peak_type=None):
        '''
        Add SequencingRun record with the details of this run.
        
        Should be called only after all tags have been added.
        ''' 
        connection.close()
        s, created = SequencingRun.objects.get_or_create(source_table=cls._meta.db_table,
                                        defaults={'name': cls.name, 
                                                  'total_tags': cls.objects.count(),
                                                  'description': description,
                                                  'cell_type': current_settings.CURRENT_CELL_TYPE,
                                                  'type': type,
                                                  'peak_type': peak_type or cls.peak_type() }
                                               )
        return s