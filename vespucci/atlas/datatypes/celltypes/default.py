'''
Created on Dec 22, 2010

@author: karmel
'''
from vespucci.atlas.datatypes.transcript import AtlasTranscript, \
    FilteredAtlasTranscript, AtlasTranscriptSource, \
    AtlasTranscriptSequence, AtlasTranscriptNonCoding, CellTypeBase, \
    AtlasTranscriptSourcePrep, AtlasTranscriptPrep, FilteredAtlasTranscriptManager
from vespucci.config import current_settings
from django.db import models


SCHEMA_BASE = 'atlas_{0}_{1}'.format(current_settings.GENOME, current_settings.CELL_TYPE.lower())

class DefaultBase(CellTypeBase):
    cell_type = current_settings.CELL_TYPE
    schema_base = SCHEMA_BASE

    @property
    def atlas_transcript(self): return AtlasTranscriptDefault
    @property
    def atlas_transcript_prep(self): return AtlasTranscriptPrepDefault
    @property
    def filtered_atlas_transcript(self): return FilteredAtlasTranscriptDefault
    @property
    def atlas_transcript_source(self): return AtlasTranscriptSourceDefault
    @property
    def atlas_transcript_source_prep(self): return AtlasTranscriptSourcePrepDefault
    @property
    def atlas_transcript_sequence(self): return AtlasTranscriptSequenceDefault
    @property
    def atlas_transcript_non_coding(self): return AtlasTranscriptNonCodingDefault

    
class AtlasTranscriptDefault(AtlasTranscript):
    cell_base = DefaultBase()
    
    class Meta(object):
        db_table = '{0}{1}"."atlas_transcript'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(current_settings.CELL_TYPE)
        verbose_name = 'Unfiltered Atlas transcript ({0})'.format(current_settings.CELL_TYPE)
        verbose_name_plural = 'Unfiltered Atlas transcripts ({0})'.format(current_settings.CELL_TYPE)

class AtlasTranscriptPrepDefault(AtlasTranscriptPrep):
    cell_base = DefaultBase()
    class Meta(object):
        db_table = '{0}_prep"."atlas_transcript'.format(SCHEMA_BASE)
        app_label = 'Transcription_{0}'.format(current_settings.CELL_TYPE)
        verbose_name = 'Preparatory Atlas transcript ({0})'.format(current_settings.CELL_TYPE)
        verbose_name_plural = 'Preparatory Atlas transcripts ({0})'.format(current_settings.CELL_TYPE)

class FilteredAtlasTranscriptDefault(AtlasTranscriptDefault, FilteredAtlasTranscript):
    cell_base = DefaultBase()
    objects = FilteredAtlasTranscriptManager()
    class Meta(object):
        proxy = True
        app_label = 'Transcription_{0}'.format(current_settings.CELL_TYPE)
        verbose_name = 'Atlas transcript ({0})'.format(current_settings.CELL_TYPE)
        verbose_name_plural = 'Atlas transcripts ({0})'.format(current_settings.CELL_TYPE)
      
class AtlasTranscriptSourcePrepDefault(AtlasTranscriptSourcePrep):
    atlas_transcript = models.ForeignKey(AtlasTranscriptPrepDefault, related_name='atlastranscriptsource')
    cell_base = DefaultBase()
    class Meta(object):
        db_table = '{0}_prep"."atlas_transcript_source'.format(SCHEMA_BASE)
        app_label = 'Transcription_{0}'.format(current_settings.CELL_TYPE)
        verbose_name = 'Preparatory Atlas transcript source ({0})'.format(current_settings.CELL_TYPE)
        verbose_name_plural = 'Preparatory Atlas transcript sources ({0})'.format(current_settings.CELL_TYPE)

class AtlasTranscriptSourceDefault(AtlasTranscriptSource):
    atlas_transcript = models.ForeignKey(AtlasTranscriptDefault, related_name='atlastranscriptsource')
    cell_base = DefaultBase()
    class Meta(object):
        db_table = '{0}{1}"."atlas_transcript_source'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(current_settings.CELL_TYPE)
        verbose_name = 'Atlas transcript source ({0})'.format(current_settings.CELL_TYPE)
        verbose_name_plural = 'Atlas transcript sources ({0})'.format(current_settings.CELL_TYPE)
       
class AtlasTranscriptSequenceDefault(AtlasTranscriptSequence):
    atlas_transcript = models.ForeignKey(AtlasTranscriptDefault)
    cell_base = DefaultBase()
    class Meta(object): 
        db_table = '{0}{1}"."atlas_transcript_sequence'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(current_settings.CELL_TYPE)
        verbose_name = 'Atlas transcript sequence region ({0})'.format(current_settings.CELL_TYPE)
        verbose_name_plural = 'Atlas transcript sequence regions ({0})'.format(current_settings.CELL_TYPE)
           
class AtlasTranscriptNonCodingDefault(AtlasTranscriptNonCoding):
    atlas_transcript = models.ForeignKey(AtlasTranscriptDefault)
    cell_base = DefaultBase()
    class Meta(object): 
        db_table = '{0}{1}"."atlas_transcript_non_coding'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(current_settings.CELL_TYPE)
        verbose_name = 'Atlas transcript non-coding region ({0})'.format(current_settings.CELL_TYPE)
        verbose_name_plural = 'Atlas transcript non-coding regions ({0})'.format(current_settings.CELL_TYPE)


class RefSeqBase(CellTypeBase):
    '''
    Empty class for use in setting up RefSeq database.
    '''
    cell_type = 'RefSeq'
