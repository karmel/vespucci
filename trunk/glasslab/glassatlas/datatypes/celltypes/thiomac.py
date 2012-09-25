'''
Created on Dec 22, 2010

@author: karmel
'''
from glasslab.glassatlas.datatypes.transcript import GlassTranscript, \
    FilteredGlassTranscript, GlassTranscriptNucleotides, GlassTranscriptSource, \
    GlassTranscriptSequence, GlassTranscriptConserved, GlassTranscriptPatterned, \
    GlassTranscriptNonCoding, CellTypeBase, GlassTranscriptSourcePrep, \
    GlassTranscriptPrep, GlassTranscriptInfrastructure, GlassTranscriptDuped, \
    FilteredGlassTranscriptManager
from glasslab.config import current_settings
from glasslab.glassatlas.datatypes.transcribed_rna import GlassTranscribedRna, \
    GlassTranscribedRnaSource
from django.db import models
from glasslab.glassatlas.datatypes.feature import PeakFeature
from glasslab.glassatlas.datatypes.metadata import TranscriptClass
from glasslab.glassatlas.datatypes.label import GlassTranscriptLabel

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
    def glass_transcript_nucleotides(self): return GlassTranscriptNucleotidesThioMac
    @property
    def glass_transcript_sequence(self): return GlassTranscriptSequenceThioMac
    @property
    def glass_transcript_non_coding(self): return GlassTranscriptNonCodingThioMac
    @property
    def glass_transcript_infrastructure(self): return GlassTranscriptInfrastructureThioMac
    @property
    def glass_transcript_patterned(self): return GlassTranscriptPatternedThioMac
    @property
    def glass_transcript_duped(self): return GlassTranscriptDupedThioMac
    @property
    def glass_transcript_conserved(self): return GlassTranscriptConservedThioMac
    @property
    def glass_transcribed_rna(self): return GlassTranscribedRnaThioMac
    @property
    def glass_transcribed_rna_source(self): return GlassTranscribedRnaSourceThioMac
    @property
    def peak_feature(self): return PeakFeatureThioMac
    @property
    def glass_transcript_label(self): return GlassTranscriptLabelThioMac
    
class GlassTranscriptThioMac(GlassTranscript):
    cell_base = ThioMacBase()
    
    #labels = models.ManyToManyField(TranscriptClass, through='GlassTranscriptLabelThioMac')
    
    class Meta:
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Unfiltered Glass transcript (%s)' % CELL_TYPE
        verbose_name_plural = 'Unfiltered Glass transcripts (%s)' % CELL_TYPE

class GlassTranscriptPrepThioMac(GlassTranscriptPrep):
    cell_base = ThioMacBase()
    class Meta:
        db_table = 'glass_atlas_%s_%s_prep"."glass_transcript' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower())
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

class GlassTranscriptNucleotidesThioMac(GlassTranscriptNucleotides):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta:
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_nucleotides' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript nucleotide sequence (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript nucleotide sequences (%s)' % CELL_TYPE
      
class GlassTranscriptSourcePrepThioMac(GlassTranscriptSourcePrep):
    glass_transcript = models.ForeignKey(GlassTranscriptPrepThioMac, related_name='glasstranscriptsource')
    cell_base = ThioMacBase()
    class Meta:
        db_table = 'glass_atlas_%s_%s_prep"."glass_transcript_source' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower())
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Preparatory Glass transcript source (%s)' % CELL_TYPE
        verbose_name_plural = 'Preparatory Glass transcript sources (%s)' % CELL_TYPE

class GlassTranscriptSourceThioMac(GlassTranscriptSource):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac, related_name='glasstranscriptsource')
    cell_base = ThioMacBase()
    class Meta:
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_source' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript source (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript sources (%s)' % CELL_TYPE
       
class GlassTranscriptSequenceThioMac(GlassTranscriptSequence):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_sequence' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript sequence region (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript sequence regions (%s)' % CELL_TYPE
           
class GlassTranscriptNonCodingThioMac(GlassTranscriptNonCoding):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_non_coding' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript non-coding region (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript non-coding regions (%s)' % CELL_TYPE
        
class GlassTranscriptInfrastructureThioMac(GlassTranscriptInfrastructure):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_infrastructure' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript infrastructure ncRNA region (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript infrastructure ncRNA regions (%s)' % CELL_TYPE
        
class GlassTranscriptPatternedThioMac(GlassTranscriptPatterned):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_patterned' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript patterned region (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript patterned regions (%s)' % CELL_TYPE

class GlassTranscriptDupedThioMac(GlassTranscriptDuped):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_duped' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript duped region (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript duped regions (%s)' % CELL_TYPE
        
class GlassTranscriptConservedThioMac(GlassTranscriptConserved):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."glass_transcript_conserved' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript conserved region (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript conserved regions (%s)' % CELL_TYPE

##################################################
# Transcribed RNA
##################################################
class GlassTranscribedRnaThioMac(GlassTranscribedRna):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac, blank=True, null=True)
    cell_base = ThioMacBase()
    class Meta:
        abstract = True 
        #db_table    = 'glass_atlas_%s_%s_rna%s"."glass_transcribed_rna' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcribed RNA (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcribed RNAs (%s)' % CELL_TYPE
        
class GlassTranscribedRnaSourceThioMac(GlassTranscribedRnaSource):
    #glass_transcribed_rna = models.ForeignKey(GlassTranscribedRnaThioMac, related_name='glasstranscribedrnasource')
    cell_base = ThioMacBase()
    class Meta:
        abstract = True 
        #db_table    = 'glass_atlas_%s_%s_rna%s"."glass_transcribed_rna_source' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcribed RNA Source (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcribed RNA Sources (%s)' % CELL_TYPE

##################################################
# Features
##################################################       
class PeakFeatureThioMac(PeakFeature):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta: 
        db_table = 'glass_atlas_%s_%s%s"."peak_feature' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower(), current_settings.STAGING)
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Peak feature (%s)' % CELL_TYPE
        verbose_name_plural = 'Peak feature (%s)' % CELL_TYPE

##################################################
# Features
##################################################       
class GlassTranscriptLabelThioMac(GlassTranscriptLabel):
    glass_transcript = models.ForeignKey(GlassTranscriptThioMac)
    cell_base = ThioMacBase()
    class Meta:
        db_table = 'glass_atlas_%s_%s_prep"."glass_transcript_label' % (current_settings.TRANSCRIPT_GENOME, CELL_TYPE.lower())
        app_label = 'Transcription_%s' % CELL_TYPE
        verbose_name = 'Glass transcript label (%s)' % CELL_TYPE
        verbose_name_plural = 'Glass transcript labels (%s)' % CELL_TYPE
