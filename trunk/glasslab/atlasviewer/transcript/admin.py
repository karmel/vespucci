'''
Created on Nov 8, 2010

@author: karmel
'''
from django.contrib import admin
from glasslab.glassatlas.datatypes.transcript import GlassTranscript,\
    GlassTranscriptSource, GlassTranscriptSequence, GlassTranscriptNonCoding,\
    GlassTranscriptConserved, GlassTranscriptPatterned,\
    GlassTranscriptNucleotides
from glasslab.glassatlas.datatypes.metadata import SequencingRun
from glasslab.config import current_settings
from glasslab.atlasviewer.shared.admin import make_all_fields_readonly,\
    ReadOnlyInline, ReadOnlyAdmin

class GlassTranscriptNucleotidesInline(ReadOnlyInline):
    model = GlassTranscriptNucleotides    
    readonly_fields = make_all_fields_readonly(model)
    
class GlassTranscriptSourceInline(ReadOnlyInline):
    model = GlassTranscriptSource    
    readonly_fields = make_all_fields_readonly(model)
    
class GlassTranscriptSequenceInline(ReadOnlyInline):
    model = GlassTranscriptSequence
    readonly_fields = make_all_fields_readonly(model)
class GlassTranscriptNonCodingInline(ReadOnlyInline):
    model = GlassTranscriptNonCoding
    readonly_fields = make_all_fields_readonly(model)
class GlassTranscriptConservedInline(ReadOnlyInline):
    model = GlassTranscriptConserved
    readonly_fields = make_all_fields_readonly(model)
class GlassTranscriptPatternedInline(ReadOnlyInline):
    model = GlassTranscriptPatterned
    readonly_fields = make_all_fields_readonly(model)
    
class GlassTranscriptAdmin(ReadOnlyAdmin):
    list_display    = ('chromosome','transcription_start','transcription_end','strand_0', 'strand_1',
                       'transcript_length', 'score', 'ucsc_browser_link', 'modified')
    list_filter     = ('chromosome','strand_0','strand_1')
    ordering        = ('chromosome','transcription_start')
    search_fields   = ['transcription_start','transcription_end',]
    inlines         = [GlassTranscriptSourceInline,
                       GlassTranscriptNucleotidesInline, 
                       GlassTranscriptSequenceInline,
                       GlassTranscriptNonCodingInline,
                       GlassTranscriptConservedInline,
                       GlassTranscriptPatternedInline,
                       ]
    
    def transcript_length(self, obj):
        return obj.transcription_end - obj.transcription_start
    transcript_length.short_description = 'Length'
    
    def ucsc_browser_link(self, obj):
        return '<a href="http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&amp;position=%s%%3A+%d-%d' \
                % (current_settings.REFERENCE_GENOME, obj.chromosome.name.strip(), 
                           obj.transcription_start, obj.transcription_end) \
                + '&amp;hgS_doLoadUrl=submit&amp;hgS_loadUrlName=http%3A%2F%2Fbiowhat.ucsd.edu%2Fkallison%2Fucsc%2Fsessions%2Fgro_seq.txt"' \
                + ' target="_blank">View</a>'
                        
    ucsc_browser_link.short_description = 'UCSC Browser' 
    ucsc_browser_link.allow_tags = True 
    
class SequencingRunAdmin(admin.ModelAdmin):
    list_display    = ('type', 'name', 'source_table', 'total_tags')
    list_filter     = ('type',)
    ordering        = ('modified','name')

admin.site.register(GlassTranscript, GlassTranscriptAdmin)
admin.site.register(SequencingRun, SequencingRunAdmin)
