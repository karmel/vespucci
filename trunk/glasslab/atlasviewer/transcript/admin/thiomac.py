'''
Created on Dec 22, 2010

@author: karmel
'''
from glasslab.atlasviewer.transcript.admin.base import GlassTranscriptAdmin,\
    GlassTranscribedRnaAdmin, GlassTranscriptSequenceInline,\
    GlassTranscriptNonCodingInline, GlassTranscriptSourceInline,\
    GlassTranscribedRnaInline, GlassTranscriptNucleotidesInline
from glasslab.glassatlas.datatypes.celltypes.thiomac import FilteredGlassTranscriptThioMac,\
    GlassTranscriptThioMac, GlassTranscribedRnaThioMac,\
    GlassTranscriptSequenceThioMac, GlassTranscriptSourceThioMac,\
    GlassTranscriptNonCodingThioMac, GlassTranscriptNucleotidesThioMac
from django.contrib import admin


class GlassTranscriptSequenceThioMacInline(GlassTranscriptSequenceInline):
    model = GlassTranscriptSequenceThioMac
class GlassTranscriptNonCodingThioMacInline(GlassTranscriptNonCodingInline):
    model = GlassTranscriptNonCodingThioMac
class GlassTranscriptSourceThioMacInline(GlassTranscriptSourceInline):
    model = GlassTranscriptSourceThioMac
class GlassTranscribedRnaThioMacInline(GlassTranscribedRnaInline):
    model = GlassTranscribedRnaThioMac
class GlassTranscriptNucleotidesThioMacInline(GlassTranscriptNucleotidesInline):
    model = GlassTranscriptNucleotidesThioMac
    
class GlassTranscriptThioMacAdmin(GlassTranscriptAdmin):
    inlines         = [GlassTranscriptSequenceThioMacInline,
                       GlassTranscriptNonCodingThioMacInline,
                       GlassTranscriptSourceThioMacInline, 
                       GlassTranscribedRnaThioMacInline, 
                       GlassTranscriptNucleotidesThioMacInline, 
                       ]
admin.site.register(FilteredGlassTranscriptThioMac, GlassTranscriptThioMacAdmin)
admin.site.register(GlassTranscriptThioMac, GlassTranscriptThioMacAdmin)
admin.site.register(GlassTranscribedRnaThioMac, GlassTranscribedRnaAdmin)