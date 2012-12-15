'''
Created on Dec 22, 2010

@author: karmel
'''
from glasslab.glassatlas.datatypes.transcript import GlassTranscript, \
    FilteredGlassTranscript, GlassTranscriptSource, \
    GlassTranscriptSequence, GlassTranscriptNonCoding, CellTypeBase, \
    GlassTranscriptSourcePrep, GlassTranscriptPrep, FilteredGlassTranscriptManager
from glasslab.config import current_settings

from django.db import models

CELL_TYPE = 'Default'
SCHEMA_BASE = '{0}'.format(current_settings.GENOME, CELL_TYPE.lower())

class DefaultBase(CellTypeBase):
    cell_type = CELL_TYPE
    schema_base = SCHEMA_BASE

    @property
    def glass_transcript(self): return GlassTranscriptThioMac
    @property
    def glass_transcript_prep(self): return GlassTranscriptPrepThioMac
    @property
    def filtered_glass_transcript(self): return FilteredGlassTranscriptThioMac
    @property
    def glass_transcript_source(self): return GlassTranscriptSourceThioMac
    @property
    def glass_transcript_source_prep(self): return GlassTranscriptSourcePrepThioMac
    @property
    def glass_transcript_sequence(self): return GlassTranscriptSequenceThioMac
    @property
    def glass_transcript_non_coding(self): return GlassTranscriptNonCodingThioMac

    
class GlassTranscriptThioMac(GlassTranscript):
    cell_base = DefaultBase()
    
    #labels = models.ManyToManyField(TranscriptClass, through='GlassTranscriptLabelThioMac')
    
    class Meta:
        db_table = '{0}{1}"."glass_transcript'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Unfiltered Glass transcript ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Unfiltered Glass transcripts ({0})'.format(CELL_TYPE)

class GlassTranscriptPrepThioMac(GlassTranscriptPrep):
    cell_base = DefaultBase()
    class Meta:
        db_table = '{0}_prep"."glass_transcript'.format(SCHEMA_BASE)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Preparatory Glass transcript ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Preparatory Glass transcripts ({0})'.format(CELL_TYPE)

class FilteredGlassTranscriptThioMac(GlassTranscriptThioMac, FilteredGlassTranscript):
    cell_base = DefaultBase()
    objects = FilteredGlassTranscriptManager()
    class Meta:
        proxy = True
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Glass transcript ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Glass transcripts ({0})'.format(CELL_TYPE)
      
class GlassTranscriptSourcePrepThioMac(GlassTranscriptSourcePrep):
    glass_transcript = models.ForeignKey(GlassTranscriptPrepThioMac, related_name='glasstranscriptsource')
    cell_base = DefaultBase()
    class Meta:
        db_table = '{0}_prep"."glass_transcript_source'.format(SCHEMA_BASE)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Preparatory Glass transcript source ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Preparatory Glass transcript sources ({0})'.format(CELL_TYPE)

class GlassTranscriptSourceThioMac(GlassTranscriptSource):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac, related_name='glasstranscriptsource')
    cell_base = DefaultBase()
    class Meta:
        db_table = '{0}{1}"."glass_transcript_source'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Glass transcript source ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Glass transcript sources ({0})'.format(CELL_TYPE)
       
class GlassTranscriptSequenceThioMac(GlassTranscriptSequence):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = DefaultBase()
    class Meta: 
        db_table = '{0}{1}"."glass_transcript_sequence'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Glass transcript sequence region ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Glass transcript sequence regions ({0})'.format(CELL_TYPE)
           
class GlassTranscriptNonCodingThioMac(GlassTranscriptNonCoding):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = DefaultBase()
    class Meta: 
        db_table = '{0}{1}"."glass_transcript_non_coding'.format(SCHEMA_BASE, current_settings.STAGING)
        app_label = 'Transcription_{0}'.format(CELL_TYPE)
        verbose_name = 'Glass transcript non-coding region ({0})'.format(CELL_TYPE)
        verbose_name_plural = 'Glass transcript non-coding regions ({0})'.format(CELL_TYPE)


class RefSeqBase(CellTypeBase):
    '''
    Empty class for use in setting up RefSeq database.
    '''
    cell_type = 'RefSeq'