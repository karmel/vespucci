'''
Created on Sep 27, 2010

@author: karmel
'''
from django.db import models, connection
from glasslab.utils.datatypes.genome_reference import Chromosome
from glasslab.utils.datatypes.basic_model import DynamicTable, BoxField
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
    
    start_end       = BoxField(max_length=255, help_text='This is a placeholder for the PostgreSQL box type.') 
    
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
            start_end box,
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
                     start_end=(int(row[1]), 0, int(row[2]), 0),
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
                     start_end=(int(row[1]), 0, int(row[2]), 0),
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
    
class HomerPeak(GlassSequencingOutput):
    '''
    Peaks from Homer output, for easy table loading and comparison.
    '''
    cluster_id      = models.CharField(max_length=255, null=True, blank=True)
    chromosome      = models.ForeignKey(Chromosome)
    strand          = models.IntegerField(max_length=1)
    start           = models.IntegerField(max_length=12)
    end             = models.IntegerField(max_length=12)
    
    start_end       = BoxField(max_length=255, help_text='This is a placeholder for the PostgreSQL box type.') 
    
    peak_score      = models.IntegerField(max_length=12)
    distance_to_tss = models.IntegerField(max_length=12)
    
    annotation          = models.CharField(max_length=255, null=True, blank=True)
    detailed_annotation = models.CharField(max_length=255, null=True, blank=True)
    nearest_promoter    = models.CharField(max_length=100, null=True, blank=True)
    promoter_id         = models.IntegerField(max_length=12, null=True, blank=True)
    nearest_unigene     = models.CharField(max_length=100, null=True, blank=True)
    nearest_refseq      = models.CharField(max_length=100, null=True, blank=True)
    nearest_ensembl     = models.CharField(max_length=100, null=True, blank=True)
    gene_name           = models.CharField(max_length=100, null=True, blank=True)
    gene_alias          = models.CharField(max_length=255, null=True, blank=True)
    gene_description    = models.CharField(max_length=255, null=True, blank=True)

    @classmethod        
    def create_table(cls, name):
        '''
        Create table that will be used for these peaks,
        dynamically named.
        '''
        cls.set_table_name('homer_peak_' + name)
        
        table_sql = """
        CREATE TABLE "%s" (
            id int4,
            cluster_id char(255),
            chromosome_id int4,
            strand int2,
            "start" int8,
            "end" int8,
            start_end box,
            "peak_score" int4,
            "distance_to_tss" int4,
            annotation char(255),
            detailed_annotation char(255),
            nearest_promoter char(100),
            promoter_id int4,
            nearest_unigene char(100),
            nearest_refseq char(100),
            nearest_ensembl char(100),
            gene_name char(100),
            gene_alias char(255),
            gene_description char(255)
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
               cls.name, cls._meta.db_table)
        execute_query(update_query)
        
    @classmethod
    def init_from_homer_row(cls, row):
        '''
        From a standard HOMER .xls file row, create a new peak.
        '''
        try:
            return cls(cluster_id=str(row[0]).strip(),
                   chromosome=Chromosome.objects.get(name=str(row[1]).strip()),
                     strand=str(row[4]).strip() == '-' and 1 or 0,
                     start=row[2] and int(row[2]) or None,
                     end=row[3] and int(row[3]) or None,
                     start_end=(int(row[2]), 0, int(row[3]), 0),
                     peak_score=row[5] and int(row[5]) or None,
                     annotation=str(row[6]).strip(),
                     detailed_annotation=str(row[7]).strip(),
                     distance_to_tss=row[8] and int(row[8]) or None,
                     nearest_promoter=str(row[9]).strip(),
                     promoter_id=row[10] and int(row[10]) or None,
                     nearest_unigene=str(row[11]).strip(),
                     nearest_refseq=str(row[12]).strip(),
                     nearest_ensembl=str(row[13]).strip(),
                     gene_name=str(row[14]).strip(),
                     gene_alias=str(row[15]).strip(),
                     gene_description=str(row[16]).strip()                     
                     )
        except Exception: 
            print row
            raise