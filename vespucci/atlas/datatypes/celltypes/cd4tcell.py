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

CELL_TYPE = 'CD4TCell'
SCHEMA_BASE = 'atlas_{0}_{1}'.format(current_settings.GENOME, CELL_TYPE.lower())

class CD4TCellBase(CellTypeBase):
    cell_type = CELL_TYPE
    schema_base = SCHEMA_BASE
    
    @property
    def atlas_transcript(self): return AtlasTranscriptThioMac
    @property
    def atlas_transcript_prep(self): return AtlasTranscriptPrepThioMac
    @property
    def filtered_atlas_transcript(self): return FilteredAtlasTranscriptThioMac
    @property
    def atlas_transcript_source(self): return AtlasTranscriptSourceThioMac
    @property
    def atlas_transcript_source_prep(self): return AtlasTranscriptSourcePrepThioMac
    @property
    def atlas_transcript_sequence(self): return AtlasTranscriptSequenceThioMac
    @property
    def atlas_transcript_non_coding(self): return AtlasTranscriptNonCodingThioMac

    
class AtlasTranscriptThioMac(AtlasTranscript):
    cell_base = CD4TCellBase()
    
    class Meta(object):
        db_table = '{0}{1}"."atlas_transcript'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Unfiltered Atlas transcript ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Unfiltered Atlas transcripts ({0})'.format(CELL_TYPE)

class AtlasTranscriptPrepThioMac(AtlasTranscriptPrep):
    cell_base = CD4TCellBase()
    class Meta(object):
        db_table = '{0}_prep"."atlas_transcript'.format(SCHEMA_BASE)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Preparatory Atlas transcript ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Preparatory Atlas transcripts ({0})'.format(CELL_TYPE)

class FilteredAtlasTranscriptThioMac(AtlasTranscriptThioMac, FilteredAtlasTranscript):
    cell_base = CD4TCellBase()
    objects = FilteredAtlasTranscriptManager()
    class Meta(object):
        proxy = True
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Atlas transcript ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Atlas transcripts ({0})'.format(CELL_TYPE)
      
class AtlasTranscriptSourcePrepThioMac(AtlasTranscriptSourcePrep):
    atlas_transcript = models.ForeignKey(AtlasTranscriptPrepThioMac, related_name='atlastranscriptsource')
    cell_base = CD4TCellBase()
    class Meta(object):
        db_table = '{0}_prep"."atlas_transcript_source'.format(SCHEMA_BASE)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Preparatory Atlas transcript source ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Preparatory Atlas transcript sources ({0})'.format(CELL_TYPE)

class AtlasTranscriptSourceThioMac(AtlasTranscriptSource):
    atlas_transcript = models.ForeignKey(AtlasTranscriptThioMac, related_name='atlastranscriptsource')
    cell_base = CD4TCellBase()
    class Meta(object):
        db_table = '{0}{1}"."atlas_transcript_source'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Atlas transcript source ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Atlas transcript sources ({0})'.format(CELL_TYPE)
       
class AtlasTranscriptSequenceThioMac(AtlasTranscriptSequence):
    atlas_transcript = models.ForeignKey(AtlasTranscriptThioMac)
    cell_base = CD4TCellBase()
    class Meta(object): 
        db_table = '{0}{1}"."atlas_transcript_sequence'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Atlas transcript sequence region ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Atlas transcript sequence regions ({0})'.format(CELL_TYPE)
           
class AtlasTranscriptNonCodingThioMac(AtlasTranscriptNonCoding):
    atlas_transcript = models.ForeignKey(AtlasTranscriptThioMac)
    cell_base = CD4TCellBase()
    class Meta(object): 
        db_table = '{0}{1}"."atlas_transcript_non_coding'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Atlas transcript non-coding region ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Atlas transcript non-coding regions ({0})'.format(CELL_TYPE)
