'''
Created on Jul 1, 2011

@author: karmel

Ideally, we want to be able to assign labels (classes) manually and automatically
to the transcripts. 

The classes below pertain to these relational labels.
'''
from django.db import models
from glasslab.utils.datatypes.genome_reference import Chromosome
from glasslab.utils.datatypes.basic_model import BoxField
from glasslab.glassatlas.datatypes.metadata import TranscriptClass

class GlassTranscriptLabel(models.Model):
    glass_transcript = None # Transcript is associated in cell-type specific declaration
    
    transcript_class        = models.ForeignKey(TranscriptClass)
     
    # We store positional fields to ensure we can re-assign labels
    # when we rebuild the transcript database anew.
    chromosome              = models.ForeignKey(Chromosome, null=True, default=None, blank=True)
    strand                  = models.IntegerField(max_length=1, null=True, default=None, blank=True)
    start_end               = BoxField(null=True, default=None, blank=True)
    
    manual                  = models.BooleanField(default=True)
    
    probability             = models.FloatField(null=True, default=None, blank=True)

    modified                = models.DateTimeField(auto_now=True)
    created                 = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        if self.glass_transcript:
            self.chromosome = self.glass_transcript.chromosome
            self.strand = self.glass_transcript.strand
            self.start_end = self.glass_transcript.start_end
            
        super(GlassTranscriptLabel, self).save(*args, **kwargs)
        
         
        