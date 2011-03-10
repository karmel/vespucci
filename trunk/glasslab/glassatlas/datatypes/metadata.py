'''
Created on Nov 8, 2010

@author: karmel
'''
from django.db import models, connection
from glasslab.config import current_settings
from glasslab.utils.datatypes.basic_model import GlassModel
from glasslab.utils.datatypes.genome_reference import Chromosome

class PeakType(GlassModel):
    type    = models.CharField(max_length=50)
    diffuse = models.BooleanField(default=False)
    
    class Meta:
        db_table    = 'glass_atlas_%s"."peak_type' % current_settings.REFERENCE_GENOME
        app_label   = 'Transcription' 
          
    def __unicode__(self):
        return self.type.strip()
    
class SequencingRun(GlassModel):
    '''
    Record of details of a given sequencing run and its total tags.
    '''
    type            = models.CharField(max_length=50, choices=[(x,x) for x in ('Gro-Seq','RNA-Seq','ChIP-Seq','Ribo-Seq')], default='Gro-Seq')
    
    cell_type       = models.CharField(max_length=50)
    name            = models.CharField(max_length=100)
    source_table    = models.CharField(max_length=100)
    description     = models.CharField(max_length=255, blank=True)
    total_tags      = models.IntegerField(max_length=12, help_text='Or peaks if this is a PeakType table.')
    percent_mapped  = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, default=None,
                                          help_text='What percent of tags were successfully mapped by Bowtie?')
    
    peak_type       = models.ForeignKey(PeakType, null=True, default=None, blank=True, help_text='Does this run produce ChIP peaks?')
    
    standard        = models.BooleanField(default=False, 
                                          help_text='Is this a standard run, that should affect expected scores and transcript boundaries?')
    requires_reload = models.BooleanField(default=False, help_text='Should this run be reloaded with the next processing cycle?')
    
    timepoint       = models.CharField(max_length=10, blank=True, null=True)
    wt              = models.BooleanField(default=False)    
    notx            = models.BooleanField(default=False)    
    kla             = models.BooleanField(default=False)    
    other_conditions= models.BooleanField(default=False)    
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table    = 'glass_atlas_%s"."sequencing_run' % current_settings.REFERENCE_GENOME
        app_label   = 'Transcription'
        
    def __unicode__(self):
        return '%s (%s, "%s")' % (self.name, self.type, self.source_table.strip())
    
    @classmethod
    def mark_all_reloaded(cls):
        '''
        Mark all runs as reloaded. Called by external processes that have reloaded runs appropriately.
        '''
        connection.close()
        cls.objects.all().update(requires_reload=False)
        
class SequencingRunAnnotation(GlassModel):
    '''
    Various freeform notes that can be attached to sequencing runs.
    '''
    sequencing_run  = models.ForeignKey(SequencingRun)
    note            = models.CharField(max_length=100)
     
    class Meta:
        db_table    = 'glass_atlas_%s"."sequencing_run_annotation' % current_settings.REFERENCE_GENOME
        app_label   = 'Transcription'
        
    def __unicode__(self):
        return '"%s" note: %s' % (self.sequencing_run.source_table.strip(), self.note)
        
class ExpectedTagCount(GlassModel):
    '''
    Per chromosome, per strand expected tag counts based on random sampling of 
    standard Gro-Seq runs.
    '''
    chromosome      = models.ForeignKey(Chromosome)
    strand          = models.IntegerField(max_length=1, help_text='0 for +, 1 for -')
    sample_count    = models.IntegerField(max_length=10)
    sample_size     = models.IntegerField(max_length=5)
    tag_count       = models.FloatField()
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
   
    class Meta:
        db_table    = 'glass_atlas_%s"."expected_tag_count' % current_settings.REFERENCE_GENOME
        app_label   = 'Transcription'
        
    def __unicode__(self):
        return '"%s" note: %s' % (self.sequencing_run.source_table.strip(), self.note)
    

    