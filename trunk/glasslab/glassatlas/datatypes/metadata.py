'''
Created on Nov 8, 2010

@author: karmel
'''
from django.db import models, connection
from glasslab.config import current_settings
from glasslab.utils.datatypes.basic_model import GlassModel
from glasslab.utils.datatypes.genome_reference import Chromosome
    
class SequencingRun(GlassModel):
    '''
    Record of details of a given sequencing run and its total tags.
    '''
    source_table    = models.CharField(max_length=100)
    
    class Meta:
        db_table    = 'glass_atlas_%s"."sequencing_run' % current_settings.GENOME
        app_label   = 'Transcription'
        
    def __unicode__(self):
        return '%s (%s, "%s")' % (self.name, self.type, self.source_table.strip())