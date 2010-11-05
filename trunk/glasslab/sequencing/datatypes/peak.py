'''
Created on Sep 27, 2010

@author: karmel
'''
from django.db import models
from glasslab.utils.datatypes.genome_reference import SequenceTranscriptionRegion,\
    Chromosome
from django.db import connection, transaction
from glasslab.sequencing.datatypes.tag import DynamicTable
        
class CurrentPeak(DynamicTable):
    '''
    From MACS::
        
        chr     start   end     length  summit  tags    -10*log10(pvalue)       fold_enrichment
        
    .. warning::
        
        CURRENTLY DEPRACATED! Because we have moved to a primarily tag-based analysis system,
        this peak model has fallen by the wayside. 
        
        It is maintained here for reference and future potential uses; 
        if any such uses arise, please update before trying to make use of this model.

    '''
    chromosome      = models.ForeignKey(Chromosome)
    start           = models.IntegerField(max_length=12)
    end             = models.IntegerField(max_length=12)
    length          = models.IntegerField(max_length=12)
    summit          = models.IntegerField(max_length=12)
    tag_count       = models.IntegerField(max_length=12)
    log_ten_p_value = models.DecimalField(max_digits=10, decimal_places=4)
    fold_enrichment = models.DecimalField(max_digits=10, decimal_places=4)
    
    start_end       = models.CharField(max_length=255, help_text='This is a placeholder for the PostgreSQL cube type.') 
    
    sequence_transcription_region   = models.ForeignKey(SequenceTranscriptionRegion, null=True, default=None)
    start_site      = models.BooleanField(default=False)
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
                
    @classmethod        
    def create_table(cls, name):
        '''
        Create table that will be used for these peaks,
        dynamically named.
        '''
        if cls.table_created: print 'Warning: CurrentPeak table has already been created.'
        cls.set_table_name('peaks_' + name)
        cls.name = name
        table_sql = """
        CREATE TABLE "%s" (
            id serial4,
            chromosome_id int4,
            "start" int8,
            "end" int8,
            "length" int4,
            summit int8,
            tag_count int4,
            log_ten_p_value decimal(10,6),
            fold_enrichment decimal(10,6),
            start_end public.cube,
            sequence_transcription_region_id int4 DEFAULT NULL,
            modified timestamp,
            created timestamp,
            PRIMARY KEY (id));
        CREATE INDEX "%s_chr_index" ON "%s" USING btree("chromosome_id");
        CREATE INDEX "%s_start_end_index" ON "%s" USING gist("start_end");
        CREATE INDEX "%s_sequence_region_idx" ON "%s" USING btree(sequence_transcription_region_id);
        """ % (cls._meta.db_table, 
               name, cls._meta.db_table,
               name, cls._meta.db_table,)
        cursor = connection.cursor()
        cursor.execute(table_sql)
        transaction.commit_unless_managed()
        
        cls.table_created = True
    
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
    
