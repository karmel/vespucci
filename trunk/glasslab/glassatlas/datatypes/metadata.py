'''
Created on Nov 8, 2010

@author: karmel
'''
from django.db import models
from glasslab.config import current_settings

class SequencingRun(models.Model):
    '''
    Record of details of a given sequencing run and its total tags.
    '''
    type            = models.CharField(max_length=50, choices=[(x,x) for x in ('Gro-Seq','RNA-Seq','ChIP-Seq','Ribo-Seq')], default='Gro-Seq')
    
    cell_type       = models.CharField(max_length=50)
    name            = models.CharField(max_length=100)
    source_table    = models.CharField(max_length=100)
    description     = models.CharField(max_length=255, blank=True)
    total_tags      = models.IntegerField(max_length=12)
    percent_mapped  = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, default=None,
                                          help_text='What percent of tags were successfully mapped by Bowtie?')
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table    = 'glass_atlas_%s"."sequencing_run' % current_settings.REFERENCE_GENOME
        app_label   = 'Transcription'
        
    def __unicode__(self):
        return '%s (%s, "%s")' % (self.name, self.type, self.source_table.strip())
    
class SequencingRunAnnotation(models.Model):
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
    
class PeakType(models.Model):
    type    = models.CharField(max_length=50)
    diffuse = models.BooleanField(default=False)
    
    class Meta:
        db_table    = 'glass_atlas_%s"."chip_seq_type' % current_settings.REFERENCE_GENOME
        app_label   = 'Transcription' 
          
    def __unicode__(self):
        return self.type.strip()
    