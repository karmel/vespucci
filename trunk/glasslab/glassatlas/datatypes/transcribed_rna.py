'''
Created on Dec 16, 2010

@author: karmel
'''
from glasslab.config import current_settings
from glasslab.glassatlas.datatypes.transcript import TranscriptBase, \
    multiprocess_all_chromosomes, TranscriptSourceBase
from glasslab.sequencing.datatypes.tag import multiprocess_glass_tags,\
    wrap_errors
from glasslab.utils.database import execute_query

def wrap_add_transcribed_rna_from_rnaseq(cls, chr_list, *args): 
    wrap_errors(cls._add_transcribed_rna_from_rnaseq, chr_list, *args)
def wrap_associate_transcribed_rna(cls, chr_list): 
    wrap_errors(cls._associate_transcribed_rna, chr_list)
def wrap_stitch_together_transcribed_rna(cls, chr_list): 
    wrap_errors(cls._stitch_together_transcribed_rna, chr_list)

MAX_GAP_RNA = 10
class GlassTranscribedRna(TranscriptBase):
    '''
    Transcribed RNA sequenced in RNA-Seq experiments.
    '''
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
                SELECT glass_atlas_%s_%s.save_transcribed_rna_from_sequencing_run(%d, %d,'%s', %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       sequencing_run.id, chr_id, 
                       sequencing_run.source_table.strip(), MAX_GAP_RNA)
            execute_query(query)
            
    ################################################
    # Transcript cleanup and refinement
    ################################################
    @classmethod
    def associate_transcribed_rna(cls):
        multiprocess_all_chromosomes(wrap_associate_transcribed_rna, cls)
    
    @classmethod
    def _associate_transcribed_rna(cls, chr_list):
        for chr_id in chr_list:
            print 'Associating transcripts with transcribed RNA for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s.associate_transcribed_rna(%d);
                SELECT glass_atlas_%s_%s.mark_transcripts_as_spliced(%d);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(), chr_id,
                       current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(), chr_id)
            execute_query(query) 
            
    @classmethod
    def stitch_together_transcribed_rna(cls):
        multiprocess_all_chromosomes(wrap_stitch_together_transcribed_rna, cls)
    
    @classmethod
    def _stitch_together_transcribed_rna(cls, chr_list):
        for chr_id in chr_list:
            print 'Stitching together transcribed RNA for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s.stitch_transcribed_rna_together(%d, %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(), 
                       chr_id, MAX_GAP_RNA)
            execute_query(query)

class GlassTranscribedRnaSource(TranscriptSourceBase):
    class Meta:
        abstract = True
        