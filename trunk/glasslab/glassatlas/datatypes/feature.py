'''
Created on Jan 17, 2011

@author: karmel

Features and annotations relevant to transcripts.
'''
from django.db import models
from glasslab.sequencing.datatypes.peak import GlassPeak
from glasslab.glassatlas.datatypes.metadata import SequencingRun, PeakType
        
class PeakFeature(models.Model):
    # Transcript is cell specific.
    glass_transcript = None
    relationship    = models.CharField(max_length=100, choices=[(x,x) 
                                                    for x in ('contains','is contained by','overlaps with','is equal to',
                                                              'is upstream of', 'is downstream of')])
    chip_seq_type   = models.ForeignKey(PeakType)
    
    class Meta:
        abstract    = True
          
    def __unicode__(self):
        return '%s %s %s' % (str(self.glass_transcript), 
                             self.relationship.strip(),
                             str(self.chip_seq_type))

class PeakFeatureInstance(models.Model):
    ''' 
    Record of an individual peak and source to a feature assigned to a glass transcript.
    '''
    # PeakFeature is cell specific.
    glass_peak      = models.ForeignKey(GlassPeak)
    sequencing_run  = models.ForeignKey(SequencingRun)
    
    distance_to_tss = models.IntegerField(max_length=12)
    
    class Meta:
        abstract    = True
          
    def __unicode__(self):
        return '%s from %s (%d to TSS)' % (str(self.peak_feature), 
                                           str(self.glass_peak), 
                                           self.distance_to_tss)

    ################################################
    # Association with transcripts
    ################################################