'''
Created on Dec 22, 2010

@author: karmel
'''
from glasslab.atlasviewer.transcript.admin.base import GlassTranscriptAdmin,\
    GlassTranscribedRnaAdmin, GlassTranscriptSequenceInline,\
    GlassTranscriptNonCodingInline, GlassTranscriptSourceInline,\
    GlassTranscribedRnaInline, GlassTranscriptNucleotidesInline,\
    PeakFeatureInline, PeakFeatureInstanceInline, PeakFeatureAdmin
from glasslab.glassatlas.datatypes.celltypes.thiomac import FilteredGlassTranscriptThioMac,\
    GlassTranscriptThioMac, GlassTranscribedRnaThioMac,\
    GlassTranscriptSequenceThioMac, GlassTranscriptSourceThioMac,\
    GlassTranscriptNonCodingThioMac, GlassTranscriptNucleotidesThioMac,\
    GlassTranscribedRnaSourceThioMac, PeakFeatureThioMac,\
    PeakFeatureInstanceThioMac
from django.contrib import admin


class GlassTranscriptSequenceThioMacInline(GlassTranscriptSequenceInline):
    model = GlassTranscriptSequenceThioMac
class GlassTranscriptNonCodingThioMacInline(GlassTranscriptNonCodingInline):
    model = GlassTranscriptNonCodingThioMac
class GlassTranscriptSourceThioMacInline(GlassTranscriptSourceInline):
    model = GlassTranscriptSourceThioMac

class GlassTranscribedRnaSourceThioMacInline(GlassTranscriptSourceInline):
    model = GlassTranscribedRnaSourceThioMac
class GlassTranscribedRnaThioMacInline(GlassTranscribedRnaInline):
    model = GlassTranscribedRnaThioMac
    
class GlassTranscriptNucleotidesThioMacInline(GlassTranscriptNucleotidesInline):
    model = GlassTranscriptNucleotidesThioMac

class PeakFeatureInstanceThioMacInline(PeakFeatureInstanceInline):
    model = PeakFeatureInstanceThioMac

class PeakFeatureThioMacInline(PeakFeatureInline):
    model = PeakFeatureThioMac
    
class GlassTranscriptThioMacAdmin(GlassTranscriptAdmin):
    inlines         = [GlassTranscriptSequenceThioMacInline,
                       GlassTranscriptNonCodingThioMacInline,
                       GlassTranscriptSourceThioMacInline, 
                       GlassTranscribedRnaThioMacInline,
                       PeakFeatureThioMacInline, 
                       GlassTranscriptNucleotidesThioMacInline, 
                       ]
    
class GlassTranscribedRnaThioMacAdmin(GlassTranscribedRnaAdmin):
    inlines         = [GlassTranscribedRnaSourceThioMacInline,]

class PeakFeatureThioMacAdmin(PeakFeatureAdmin):
    inlines = [PeakFeatureInstanceThioMacInline,]
     
    
admin.site.register(FilteredGlassTranscriptThioMac, GlassTranscriptThioMacAdmin)
admin.site.register(GlassTranscriptThioMac, GlassTranscriptThioMacAdmin)
admin.site.register(GlassTranscribedRnaThioMac, GlassTranscribedRnaThioMacAdmin)
admin.site.register(PeakFeatureThioMac, PeakFeatureThioMacAdmin)

