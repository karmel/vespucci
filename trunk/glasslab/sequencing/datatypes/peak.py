'''
Created on Sep 27, 2010

@author: karmel
'''
from django.db import models
from glasslab.utils.datatypes.genome_reference import TranscriptionStartSite,\
    ChromosomeLocationAnnotation
from django.db import connection, transaction
        
class EnrichedPeak(models.Model):
    '''
    From MACS::
        
        chr     start   end     length  summit  tags    -10*log10(pvalue)       fold_enrichment

    '''
    chromosome      = models.CharField(max_length=20)
    start           = models.IntegerField(max_length=12)
    end             = models.IntegerField(max_length=12)
    length          = models.IntegerField(max_length=12)
    summit          = models.IntegerField(max_length=12)
    tag_count       = models.IntegerField(max_length=12)
    log_ten_p_value = models.DecimalField(max_digits=10, decimal_places=4)
    fold_enrichment = models.DecimalField(max_digits=10, decimal_places=4)
    
    transcription_start_site        = models.ForeignKey(TranscriptionStartSite, null=True, default=None)
    distance                        = models.IntegerField(max_length=12, null=True, default=None)
    chromosome_location_annotation  = models.ForeignKey(ChromosomeLocationAnnotation, null=True, default=None)
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
    
    @classmethod
    def init_from_macs_row(cls, row):
        '''
        From a standard tab-delimited MACS peak file, create model instance.
        '''
        return cls(chromosome=str(row[0]).strip(),
                     start=int(row[1]),
                     end=int(row[2]),
                     length=int(row[3]),
                     summit=int(row[4]),
                     tag_count=int(row[5]),
                     log_ten_p_value=str(row[6]),
                     fold_enrichment=str(row[7]))
    
    @classmethod    
    def find_transcriptions_start_sites(cls, genome):
        '''
        The logic here: for any given peak, the most likely expressed gene is the 
        one whose transcriptions start site is closest to the summit of the peak
        in question. Note that the determination of nearest TSS is direction dependent-- 
        so if the TSS is on the complement strand, than the start is actually the 
        field labeled "end."
        
        This is executed in a single SQL query that assigns the TSS whose
        true start is closest to the peak's summit.
        '''
        
        update_sql = """
        UPDATE 
            "current_projects"."enriched_peaks_%s" peak2
        SET 
            transcription_start_site_id = derived2.tss_id,
            distance = derived2.distance
        FROM (
            SELECT 
                ROW_NUMBER() OVER (PARTITION BY derived.peak_id ORDER BY derived.abs_distance ASC) as pk,
                derived.peak_id,
                derived.tss_id,
                derived.distance
            FROM (
                SELECT 
                    peak.id as peak_id,
                    tss.id as tss_id,
                    ((peak.summit + peak.start) - 
                        (CASE     
                            WHEN tss.direction = '0' THEN tss.start
                            WHEN tss.direction = '1' THEN tss.end
                        END)
                    ) as distance,
                    abs((peak.summit + peak.start) - 
                        (CASE     
                            WHEN tss.direction = '0' THEN tss.start
                            WHEN tss.direction = '1' THEN tss.end
                        END)
                    ) as abs_distance
                FROM "current_projects"."enriched_peaks_%s" peak
                JOIN 
                    "genome_reference"."transcription_start_site" tss
                ON 
                    peak.chromosome = tss.chromosome
                WHERE 
                    tss.genome_id = %%s
                ORDER BY abs_distance ASC
            ) derived
        ) derived2
        WHERE 
            derived2.pk = '1'
            AND peak2.id = derived2.peak_id;
        """ % (cls._meta.db_table, cls._meta.db_table)
        cursor = connection.cursor()
        cursor.execute(update_sql, [genome])
        transaction.commit_unless_managed()
                 
class CurrentPeak(EnrichedPeak):
    name = None
    table_created = None
    
    @classmethod        
    def create_table(cls, name):
        '''
        Create table that will be used for these peaks,
        dynamically named.
        '''
        if cls.table_created: print 'Warning: CurrentPeak table has already been created.'
        
        cls.name = name
        cls._meta.db_table = 'current_projects"."enriched_peaks_%s' % name
        table_sql = """
        CREATE TABLE "%s" (
            id serial4,
            chromosome char(20),
            "start" int8,
            "end" int8,
            "length" int4,
            summit int8,
            tag_count int4,
            log_ten_p_value decimal(10,6),
            fold_enrichment decimal(10,6),
            transcription_start_site_id int4 DEFAULT NULL,
            distance int4 DEFAULT NULL,
            chromosome_location_annotation_id int4 DEFAULT NULL,
            modified timestamp,
            created timestamp,
            PRIMARY KEY (id));
        CREATE INDEX "%s_index" ON "%s" ("chromosome", "start", "end");
        """ % (cls._meta.db_table, name, cls._meta.db_table)
        cursor = connection.cursor()
        cursor.execute(table_sql)
        transaction.commit_unless_managed()
        
        cls.table_created = True
