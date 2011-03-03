'''
Created on Jan 17, 2011

@author: karmel

Features and annotations relevant to transcripts.
'''
from django.db import models, connection
from glasslab.sequencing.datatypes.peak import GlassPeak,\
    multiprocess_glass_peaks
from glasslab.glassatlas.datatypes.metadata import SequencingRun, PeakType
from glasslab.sequencing.datatypes.tag import wrap_errors
from glasslab.config import current_settings
from glasslab.utils.database import execute_query
from glasslab.glassatlas.datatypes.transcript import multiprocess_all_chromosomes
from glasslab.utils.datatypes.basic_model import GlassModel
from django.db.models.aggregates import Avg


def wrap_add_features_from_chipseq(cls, chr_list, *args): wrap_errors(cls._add_features_from_chipseq, chr_list, *args)
def wrap_update_peak_features(cls, chr_list, *args): wrap_errors(cls._update_peak_features, chr_list, *args)

class PeakFeature(GlassModel):
    # Transcript is cell specific.
    glass_transcript = None
    relationship    = models.CharField(max_length=100)
    peak_type   = models.ForeignKey(PeakType)
    
    class Meta:
        abstract    = True
          
    def __unicode__(self):
        return '%s %s %s (Avg Dist from Peak Center to TSS: %d)' % (str(self.glass_transcript), 
                             self.relationship.strip(),
                             str(self.peak_type),
                             self.peak_feature_instance_set.aggregate(dist=Avg('distance_to_tss'))['dist'])
        
    @classmethod 
    def add_from_peaks(cls,  tag_table):
        connection.close()
        sequencing_run = SequencingRun.objects.get(source_table=tag_table)
        if sequencing_run.type.strip() == 'ChIP-Seq':
            cls.add_features_from_chipseq(tag_table, sequencing_run)
    
    ################################################
    # ChIP-Seq to peak feature
    ################################################
    @classmethod 
    def add_features_from_chipseq(cls,  tag_table, sequencing_run):
        multiprocess_glass_peaks(wrap_add_features_from_chipseq, cls, sequencing_run)
        
    @classmethod
    def _add_features_from_chipseq(cls, chr_list, sequencing_run):
        for chr_id in chr_list:
            print 'Adding peak features for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s.insert_associated_peak_features_from_run(%d, %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       sequencing_run.id, chr_id)
            execute_query(query)
    
    @classmethod 
    def update_peak_features_by_run(cls):
        '''
        Update peak features for all transcripts for runs where requires_reload = true
        '''
        multiprocess_all_chromosomes(wrap_update_peak_features, cls, True)
        
    @classmethod
    def _update_peak_features(cls, chr_list, run_requires_reload_only=True):
        for chr_id in chr_list:
            print 'Updating peak features for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s.update_peak_features(%d, %s);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       chr_id, 
                       run_requires_reload_only and 'true' or 'false')
            execute_query(query)
            
class PeakFeatureInstance(GlassModel):
    ''' 
    Record of an individual peak and source to a feature assigned to a glass transcript.
    '''
    # PeakFeature is cell specific.
    glass_peak_id   = models.IntegerField(max_length=12)
    sequencing_run  = models.ForeignKey(SequencingRun)
    
    distance_to_tss = models.IntegerField(max_length=12)
    
    class Meta:
        abstract    = True
          
    def __unicode__(self):
        return '%s from %s (%d to TSS)' % (str(self.peak_feature), 
                                           str(self.sequencing_run), 
                                           self.distance_to_tss)

