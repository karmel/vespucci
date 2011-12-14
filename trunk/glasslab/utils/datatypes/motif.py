'''
Created on Dec 7, 2011

@author: karmel
'''
from glasslab.utils.datatypes.basic_model import GlassModel, BoxField
from django.db import models
from glasslab.utils.datatypes.genome_reference import Chromosome

class Motif(GlassModel):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    
    class Meta: 
        db_table    = 'homer_motifs"."motif'
        app_label   = 'Genetics'

    def __unicode__(self): return self.name
    
class BindingSite(GlassModel):
    motif = models.ForeignKey(Motif)
    chromosome = models.ForeignKey(Chromosome)
    start = models.IntegerField(max_length=12)
    end = models.IntegerField(max_length=12)
    score = models.IntegerField(max_length=6)
    
    start_end = BoxField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL box type.')
    
    strain_start = models.IntegerField(max_length=12)
    strain_end = models.IntegerField(max_length=12)
    strain_start_end = BoxField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL box type.')
    
    class Meta: 
        db_table    = 'homer_motifs"."binding_site'
        app_label   = 'Homer Motifs'

    def __unicode__(self): return '%s at %s: %d - %d' % (self.motif.name, self.chromosome.name, self.start, self.end) 