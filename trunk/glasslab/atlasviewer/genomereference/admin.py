'''
Created on Nov 8, 2010

@author: karmel
'''
from django.contrib import admin
from glasslab.utils.datatypes.genome_reference import SequenceIdentifier,\
    SequenceDetail, SequenceTranscriptionRegion, SequenceExon,\
    SequenceKeggPathway, PatternedTranscriptionRegion,\
    ConservedTranscriptionRegion, NonCodingTranscriptionRegion, NonCodingRna
from glasslab.config import current_settings
from glasslab.atlasviewer.shared.admin import ReadOnlyInline,\
    make_all_fields_readonly, ReadOnlyAdmin


class SequenceDetailInline(ReadOnlyInline):
    model = SequenceDetail
    readonly_fields = make_all_fields_readonly(model)

class SequenceTranscriptionRegionInline(ReadOnlyInline):
    model = SequenceTranscriptionRegion
    readonly_fields = make_all_fields_readonly(model)

class SequenceKeggPathwayInline(ReadOnlyInline):
    model = SequenceKeggPathway
    readonly_fields = make_all_fields_readonly(model)
    
class SequenceIdentifierAdmin(ReadOnlyAdmin):
    list_display    = ('sequence_identifier', 'gene_name', 'ucsc_browser_link')
    ordering        = ('sequence_identifier',)
    search_fields   = ('sequence_identifier', 'sequencedetail__gene_name')
    
    inlines         = [SequenceDetailInline,
                       SequenceTranscriptionRegionInline,
                       SequenceKeggPathwayInline
                       ]
    
    def gene_name(self, obj):
        return obj.sequence_detail and obj.sequence_detail.gene_name or ''
    
    def ucsc_browser_link(self, obj):
        if not obj.sequence_transcription_region: 
            return 'http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&amp;position=%s' \
                    % (current_settings.REFERENCE_GENOME, obj.sequence_identifier)
                    
        return '<a href="http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&amp;position=%s%%3A+%d-%d" target="_blank">View</a>' \
                        % (current_settings.REFERENCE_GENOME, 
                           obj.sequence_transcription_region.chromosome.name.strip(), 
                           obj.sequence_transcription_region.transcription_start, 
                           obj.sequence_transcription_region.transcription_end)

    ucsc_browser_link.short_description = 'UCSC Browser' 
    ucsc_browser_link.allow_tags = True 
    
class NonCodingTranscriptionRegionInline(ReadOnlyInline):
    model = NonCodingTranscriptionRegion
    readonly_fields = make_all_fields_readonly(model)
    
class NonCodingRnaAdmin(ReadOnlyAdmin):
    list_display    = ('type', 'description', 'ucsc_browser_link')
    list_filter     = ('type',)
    ordering        = ('description',)
    search_fields   = ('description',)
    
    inlines         = [NonCodingTranscriptionRegionInline, ]
    
    def ucsc_browser_link(self, obj):
        if not obj.non_coding_transcription_region: 
            return 'http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&amp;position=%s' \
                    % (current_settings.REFERENCE_GENOME, obj.name)
                    
        return '<a href="http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&amp;position=%s%%3A+%d-%d" target="_blank">View</a>' \
                        % (current_settings.REFERENCE_GENOME, 
                           obj.non_coding_transcription_region.chromosome.name.strip(), 
                           obj.non_coding_transcription_region.transcription_start, 
                           obj.non_coding_transcription_region.transcription_end)

    ucsc_browser_link.short_description = 'UCSC Browser' 
    ucsc_browser_link.allow_tags = True 

class SequenceExonInline(ReadOnlyInline):
    model = SequenceExon
    readonly_fields = make_all_fields_readonly(model)
    
class GlassTranscriptionRegionAdmin(ReadOnlyAdmin):
    list_display    = ['chromosome', 'strand', 'transcription_start', 'transcription_end']
    list_filter     = ['chromosome', 'strand']
    search_fields   = ['transcription_start','transcription_end']

class SequenceTranscriptionRegionAdmin(GlassTranscriptionRegionAdmin):
    list_display    = ['sequence_identifier'] + GlassTranscriptionRegionAdmin.list_display
    search_fields   = ['sequence_identifier__sequence_identifier'] + GlassTranscriptionRegionAdmin.search_fields
    inlines         = [SequenceExonInline, ]
    
class NonCodingTranscriptionRegionAdmin(GlassTranscriptionRegionAdmin):
    list_display    = ['non_coding_rna'] + GlassTranscriptionRegionAdmin.list_display
    search_fields   = ['non_coding_rna__name'] + GlassTranscriptionRegionAdmin.search_fields
    
class ConservedTranscriptionRegionAdmin(GlassTranscriptionRegionAdmin):
    list_display    = ['chromosome', 'transcription_start', 'transcription_end', 'score']
    list_filter     = ['chromosome', ]
    
class PatternedTranscriptionRegionAdmin(GlassTranscriptionRegionAdmin):
    list_display    = ['type', 'name'] + GlassTranscriptionRegionAdmin.list_display
    list_filter     = ['type'] + GlassTranscriptionRegionAdmin.list_filter
    search_fields   = ['name'] + GlassTranscriptionRegionAdmin.search_fields
    
admin.site.register(SequenceIdentifier, SequenceIdentifierAdmin)
admin.site.register(NonCodingRna, NonCodingRnaAdmin)
admin.site.register(SequenceTranscriptionRegion, SequenceTranscriptionRegionAdmin)
admin.site.register(NonCodingTranscriptionRegion, NonCodingTranscriptionRegionAdmin)
admin.site.register(ConservedTranscriptionRegion, ConservedTranscriptionRegionAdmin)
admin.site.register(PatternedTranscriptionRegion, PatternedTranscriptionRegionAdmin)
