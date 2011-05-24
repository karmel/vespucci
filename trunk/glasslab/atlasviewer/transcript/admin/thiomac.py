'''
Created on Dec 22, 2010

@author: karmel
'''
from glasslab.atlasviewer.transcript.admin.base import GlassTranscriptAdmin,\
    GlassTranscribedRnaAdmin, GlassTranscriptSequenceInline,\
    GlassTranscriptNonCodingInline, GlassTranscriptSourceInline,\
    GlassTranscribedRnaInline, GlassTranscriptNucleotidesInline,\
    PeakFeatureInline, PeakFeatureAdmin,\
    GlassTranscriptPrepAdmin, GlassTranscriptSourcePrepInline,\
    GlassTranscriptDupedInline
from glasslab.glassatlas.datatypes.celltypes.thiomac import FilteredGlassTranscriptThioMac,\
    GlassTranscriptThioMac, GlassTranscribedRnaThioMac,\
    GlassTranscriptSequenceThioMac, GlassTranscriptSourceThioMac,\
    GlassTranscriptNonCodingThioMac, GlassTranscriptNucleotidesThioMac,\
    GlassTranscribedRnaSourceThioMac, PeakFeatureThioMac,\
    GlassTranscriptSourcePrepThioMac, GlassTranscriptPrepThioMac,\
    GlassTranscriptDupedThioMac
from django.contrib import admin


class GlassTranscriptSequenceThioMacInline(GlassTranscriptSequenceInline):
    model = GlassTranscriptSequenceThioMac
class GlassTranscriptNonCodingThioMacInline(GlassTranscriptNonCodingInline):
    model = GlassTranscriptNonCodingThioMac
class GlassTranscriptDupedThioMacInline(GlassTranscriptDupedInline):
    model = GlassTranscriptDupedThioMac
class GlassTranscriptSourceThioMacInline(GlassTranscriptSourceInline):
    model = GlassTranscriptSourceThioMac

class GlassTranscriptSourcePrepThioMacInline(GlassTranscriptSourcePrepInline):
    model = GlassTranscriptSourcePrepThioMac

class GlassTranscribedRnaSourceThioMacInline(GlassTranscriptSourceInline):
    model = GlassTranscribedRnaSourceThioMac
class GlassTranscribedRnaThioMacInline(GlassTranscribedRnaInline):
    model = GlassTranscribedRnaThioMac
    
class GlassTranscriptNucleotidesThioMacInline(GlassTranscriptNucleotidesInline):
    model = GlassTranscriptNucleotidesThioMac

class PeakFeatureThioMacInline(PeakFeatureInline):
    model = PeakFeatureThioMac
    
class GlassTranscriptThioMacAdmin(GlassTranscriptAdmin):
    inlines         = [GlassTranscriptSequenceThioMacInline,
                       GlassTranscriptNonCodingThioMacInline,
                       GlassTranscriptDupedThioMacInline,
                       GlassTranscriptSourceThioMacInline, 
                       GlassTranscribedRnaThioMacInline,
                       PeakFeatureThioMacInline, 
                       GlassTranscriptNucleotidesThioMacInline, 
                       ]
    
class GlassTranscriptPrepThioMacAdmin(GlassTranscriptPrepAdmin):
    inlines         = [GlassTranscriptSourcePrepThioMacInline, 
                       ]
    
class GlassTranscribedRnaThioMacAdmin(GlassTranscribedRnaAdmin):
    inlines         = [GlassTranscribedRnaSourceThioMacInline,]

class PeakFeatureThioMacAdmin(PeakFeatureAdmin):
    pass

admin.site.register(FilteredGlassTranscriptThioMac, GlassTranscriptThioMacAdmin)
admin.site.register(GlassTranscriptThioMac, GlassTranscriptThioMacAdmin)
admin.site.register(GlassTranscriptPrepThioMac, GlassTranscriptPrepThioMacAdmin)
admin.site.register(GlassTranscribedRnaThioMac, GlassTranscribedRnaThioMacAdmin)
admin.site.register(PeakFeatureThioMac, PeakFeatureThioMacAdmin)

