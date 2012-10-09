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

CELL_TYPE = 'ThioMac'

class ThioMacBase(CellTypeBase):
    cell_type = CELL_TYPE
           
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
    cell_base = ThioMacBase()
    
    #labels = models.ManyToManyField(TranscriptClass, through='GlassTranscriptLabelThioMac')
    
    class Meta:
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript' % (current_settings.GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Unfiltered Glass transcript (%s)' % CELL_TYPE
        verbose_name_plural = 'Unfiltered Glass transcripts (%s)' % CELL_TYPE

class GlassTranscriptPrepThioMac(GlassTranscriptPrep):
    cell_base = ThioMacBase()
    class Meta:
        db_table = 'glass_atlas_%s_%s_prep"."glass_transcript' % (current_settings.GENOME, CELL_TYPE.lower())
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Preparatory Glass transcript (%s)' % CELL_TYPE
        verbose_name_plural = 'Preparatory Glass transcripts (%s)' % CELL_TYPE

class FilteredGlassTranscriptThioMac(GlassTranscriptThioMac, FilteredGlassTranscript):
    cell_base = ThioMacBase()
    objects = FilteredGlassTranscriptManager()
    class Meta:
        proxy = True
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcripts (%s)' % CELL_TYPE
      
class GlassTranscriptSourcePrepThioMac(GlassTranscriptSourcePrep):
    glass_transcript = models.ForeignKey(GlassTranscriptPrepThioMac, related_name='glasstranscriptsource')
    cell_base = ThioMacBase()
    class Meta:
        db_table = 'glass_atlas_%s_%s_prep"."glass_transcript_source' % (current_settings.GENOME, CELL_TYPE.lower())
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Preparatory Glass transcript source (%s)' % CELL_TYPE
        verbose_name_plural = 'Preparatory Glass transcript sources (%s)' % CELL_TYPE

class GlassTranscriptSourceThioMac(GlassTranscriptSource):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac, related_name='glasstranscriptsource')
    cell_base = ThioMacBase()
    class Meta:
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_source' % (current_settings.GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript source (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript sources (%s)' % CELL_TYPE
       
class GlassTranscriptSequenceThioMac(GlassTranscriptSequence):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_sequence' % (current_settings.GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript sequence region (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript sequence regions (%s)' % CELL_TYPE
           
class GlassTranscriptNonCodingThioMac(GlassTranscriptNonCoding):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_non_coding' % (current_settings.GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript non-coding region (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript non-coding regions (%s)' % CELL_TYPE
