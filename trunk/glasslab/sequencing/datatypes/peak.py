'''
Created on Sep 27, 2010

@author: karmel
'''
from django.db import models
from glasslab.utils.datatypes.genome_reference import TranscriptionStartSite,\
    Genome, ChromosomeLocationAnnotationFactory
from django.db import connection, transaction
        
class CurrentPeak(models.Model):
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
    
    transcription_start_site            = models.ForeignKey(TranscriptionStartSite, null=True, default=None)
    distance                            = models.IntegerField(max_length=12, null=True, default=None)
    chromosome_location_annotation_id   = models.IntegerField(max_length=11, null=True, default=None)
    chromosome_location_annotation_intergenic_id   = models.IntegerField(max_length=11, null=True, default=None)
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
    
    name = None
    table_created = None
    
    _chromosome_location_annotation = None
    @property
    def chromosome_location_annotation(self):
        if not self._chromosome_location_annotation: 
            genome = self.transcription_start_site.genome.genome
            if self.chromosome_location_annotation_id:
                id = self.chromosome_location_annotation_id
                model = ChromosomeLocationAnnotationFactory.get_model(genome)
            elif self.chromosome_location_annotation_intergenic_id:
                id = self.chromosome_location_annotation_intergenic_id
                model = ChromosomeLocationAnnotationFactory.get_intergenic(genome)
            self._chromosome_location_annotation = model.objects.get(id=id)
        return self._chromosome_location_annotation
    
    @classmethod
    def set_table_name(cls, table_name):
        '''
        Set table name for class, incorporating into schema specification.
        '''
        cls._meta.db_table = 'current_projects"."%s' % table_name
                
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
            chromosome_location_annotation_intergenic_id int4 DEFAULT NULL,
            modified timestamp,
            created timestamp,
            PRIMARY KEY (id));
        CREATE INDEX "%s_index" ON "%s" ("chromosome", "start", "end");
        CREATE INDEX "%s_index_tss" ON "%s" USING btree(transcription_start_site_id);
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
        # TSS_MAX_DISTANCE ensures that the chosen start site is either the nearest
        # or, if the nearest is still more than TSS_MAX_DISTANCE away,
        # then the nearest that is also in the correct direction of transcription
        # such that the peak falls in front of the TSS, rather than after it,
        # where "before" and "after" are defined according to the direction of transcription.
        TSS_MAX_DISTANCE = '10000'
        update_sql = """
        UPDATE 
            "%s" peak2
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
                    tss.direction as tss_direction,
                    peak.id as peak_id,
                    tss.id as tss_id,
                    ((CASE     
                        WHEN tss.direction = '0' THEN tss.start
                        WHEN tss.direction = '1' THEN tss.end
                    END) - (peak.summit + peak.start)
                    ) as distance,
                    abs((CASE     
                            WHEN tss.direction = '0' THEN tss.start
                            WHEN tss.direction = '1' THEN tss.end
                        END) - (peak.summit + peak.start)
                    ) as abs_distance
                FROM "%s" peak
                JOIN 
                    "%s" tss
                ON 
                    peak.chromosome = tss.chromosome
                JOIN 
                    "%s" genome
                ON 
                    tss.genome_id = genome.id
                WHERE 
                    genome.genome = %%s
                ORDER BY abs_distance ASC
            ) derived
            -- WHERE
                -- (derived.tss_direction = '0' and derived.distance > '-%s') 
                        -- Transcription direction is +, so find make sure the TSS is no more than 10kbp in the neg direction  
                -- OR (derived.tss_direction = '1' and derived.distance < '%s')
                        -- Transcription direction is -, so find make sure the TSS is no more than 10kbp in the pos direction
        ) derived2
        WHERE 
            derived2.pk = '1'
            AND peak2.id = derived2.peak_id;
        """ % (cls._meta.db_table, cls._meta.db_table, 
               TranscriptionStartSite._meta.db_table,
               Genome._meta.db_table,
               TSS_MAX_DISTANCE, TSS_MAX_DISTANCE)
        cursor = connection.cursor()
        cursor.execute(update_sql, [genome])
        transaction.commit_unless_managed()
            
    @classmethod
    def _find_chromosome_location_annotation(cls, genome, type=None, get_model=None):
        '''
        Find the chromosome location annotation that
        each peak falls into, and update all peaks accordingly.
        '''
        if not get_model: 
            get_model = ChromosomeLocationAnnotationFactory.get_model
        update_sql = """
        UPDATE 
            "%s" peak
        SET 
            %s = loc.id
        FROM 
            "%s" loc
        WHERE 
            peak.chromosome = loc.chromosome
            AND ((peak.summit + peak.start) >= loc.start 
                AND  (peak.summit + peak.start) <= loc.end)
            AND peak.chromosome_location_annotation_id IS NULL
        ;
        """ % (cls._meta.db_table, 
               type == 'Intergenic' and 'chromosome_location_annotation_intergenic_id' \
                                    or 'chromosome_location_annotation_id',
               get_model(genome)._meta.db_table)
        cursor = connection.cursor()
        cursor.execute(update_sql)
        transaction.commit_unless_managed()
        
    @classmethod
    def find_chromosome_location_annotation(cls, genome):
        cls._find_chromosome_location_annotation(genome)
        cls.find_chromosome_location_annotation_intergenic(genome)
        
    @classmethod
    def find_chromosome_location_annotation_intergenic(cls, genome):
        '''
        Find the intergenic chromosome location annotation that
        each peak falls into if the intron/exon/other comparisons failed to return 
        results. 
        '''
        cls._find_chromosome_location_annotation(genome, type='Intergenic', 
                            get_model=ChromosomeLocationAnnotationFactory.get_intergenic)