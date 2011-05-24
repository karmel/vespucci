'''
Created on Dec 16, 2010

@author: karmel
'''
from glasslab.config import current_settings
from glasslab.glassatlas.datatypes.transcript import TranscriptionRegionBase, \
    multiprocess_all_chromosomes, TranscriptSourceBase, MAX_GAP, TAG_EXTENSION
    
from glasslab.sequencing.datatypes.tag import multiprocess_glass_tags,\
    wrap_errors
from glasslab.utils.database import execute_query
from django.db import models

def wrap_add_transcribed_rna_from_rnaseq(cls, chr_list, *args): 
    wrap_errors(cls._add_transcribed_rna_from_rnaseq, chr_list, *args)
def wrap_associate_transcribed_rna(cls, chr_list): 
    wrap_errors(cls._associate_transcribed_rna, chr_list)
def wrap_stitch_together_transcribed_rna(cls, chr_list): 
    wrap_errors(cls._stitch_together_transcribed_rna, chr_list)
def wrap_set_scores(cls, chr_list): wrap_errors(cls._set_scores, chr_list)

MAX_GAP_RNA = MAX_GAP
MIN_SCORE_RNA = 3
class GlassTranscribedRna(TranscriptionRegionBase):
    '''
    Transcribed RNA sequenced in RNA-Seq experiments.
    '''
    score               = models.FloatField(null=True, default=None)
    
    class Meta:
        abstract = True
        
    ################################################
    # RNA-Seq to transcripts
    ################################################            
    @classmethod 
    def add_transcribed_rna_from_rnaseq(cls,  tag_table, sequencing_run):
        multiprocess_glass_tags(wrap_add_transcribed_rna_from_rnaseq, cls, sequencing_run)
        
    @classmethod
    def _add_transcribed_rna_from_rnaseq(cls, chr_list, sequencing_run):
        for chr_id in chr_list:
            print 'Adding transcribed RNA for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s_rna%s.save_transcribed_rna_from_sequencing_run(%d, %d,'%s', %d, %d, NULL);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       current_settings.STAGING,
                       sequencing_run.id, chr_id, 
                       sequencing_run.source_table.strip(), 
                       MAX_GAP_RNA, TAG_EXTENSION)
            execute_query(query)
            
    ################################################
    # Transcript cleanup and refinement
    ################################################
    @classmethod
    def stitch_together_transcribed_rna(cls):
        multiprocess_all_chromosomes(wrap_stitch_together_transcribed_rna, cls)
    
    @classmethod
    def _stitch_together_transcribed_rna(cls, chr_list):
        for chr_id in chr_list:
            print 'Stitching together transcribed RNA for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s_rna%s.save_transcribed_rna_from_existing(%d, %d, %s);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       current_settings.STAGING,
                       chr_id, MAX_GAP_RNA,'false')
            execute_query(query)
    
    @classmethod
    def associate_transcribed_rna(cls):
        multiprocess_all_chromosomes(wrap_associate_transcribed_rna, cls)
    
    @classmethod
    def _associate_transcribed_rna(cls, chr_list):
        for chr_id in chr_list:
            print 'Associating transcripts with transcribed RNA for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s%s.associate_transcribed_rna(%d);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       current_settings.STAGING, chr_id)
            execute_query(query) 
            
    @classmethod
    def set_scores(cls):
        multiprocess_all_chromosomes(wrap_set_scores, cls)
    
    @classmethod
    def _set_scores(cls, chr_list):
        for chr_id in chr_list:
            print 'Scoring transcribed_rna for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s%s.calculate_scores_transcribed_rna(%d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(), 
                       current_settings.STAGING, chr_id)
            execute_query(query) 


class GlassTranscribedRnaSource(TranscriptSourceBase):
    class Meta:
        abstract = True
        