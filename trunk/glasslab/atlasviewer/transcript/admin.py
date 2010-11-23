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
    ReadOnlyInline, ReadOnlyAdmin, ReadOnlyInput
from django.db import models
import re

class NucleotideSequenceInput(ReadOnlyInput):
    '''
    Subclassed to add custom formatting.
    '''
    def value_for_display(self, value):
        if value is None or value is '': return '&nbsp;'
        # Force line breaks
        step = 135
        value = ' '.join([value[start:start + step] for start in xrange(0,len(value),step)])
        
        value = self.wrap_codon(value, ['TAA','TAG','TGA'], 'stop-codon')
        value = self.wrap_codon(value, ['ATT','ATC','ACT'], 'antisense-stop-codon')
        value = self.wrap_codon(value, ['ATG'], 'start-codon')
        value = self.wrap_codon(value, ['TAC'], 'antisense-start-codon')
        
        # And add a key at the end
        key = '<br /><br />'
        for codon_type in ('stop','antisense-stop','start','antisense-start'):
            key += '<span class="%s-codon">%s codon</span>&nbsp;&nbsp;&nbsp;&nbsp;' % (
                                                            codon_type,
                                                            codon_type.replace('-',' '))
        return value + key
    
    def wrap_codon(self, value, codons, css_class):
        for codon in codons:
            find = '(?P<codon>' + '\s*'.join(codon) + ')'
            value = re.sub(find, '<span class="%s">\g<codon></span>' % css_class, value)
        return value
    
class GlassTranscriptNucleotidesInline(ReadOnlyInline):
    model = GlassTranscriptNucleotides    
    #readonly_fields = make_all_fields_readonly(model)
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.attname == 'sequence':
            kwargs['widget'] = NucleotideSequenceInput
        return super(GlassTranscriptNucleotidesInline, self).formfield_for_dbfield(db_field, **kwargs)
    
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
    def render_change_form(self, request, context, *args, **kwargs):
        '''
        Add in variables to display in custom template. 
        Added to model._meta because that gets passed in to the form context.
        '''
        extra = {
            'patterned_region_count': GlassTranscriptPatterned.objects.filter(glass_transcript__id=context['object_id']).count(),
            'conserved_region_count': GlassTranscriptConserved.objects.filter(glass_transcript__id=context['object_id']).count()
        }

        context.update(extra) 
        return super(GlassTranscriptAdmin, self).render_change_form(request, context, *args, **kwargs)
        
    list_display    = ('chromosome','transcription_start','transcription_end','strand_0', 'strand_1',
                       'transcript_length', 'score', 'ucsc_browser_link', 'modified')
    list_filter     = ('chromosome','strand_0','strand_1')
    ordering        = ('chromosome','transcription_start')
    search_fields   = ['transcription_start','transcription_end',]
    inlines         = [GlassTranscriptSequenceInline,
                       GlassTranscriptNonCodingInline,
                       GlassTranscriptSourceInline, 
                       GlassTranscriptNucleotidesInline, 
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
