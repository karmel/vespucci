'''
Created on Nov 8, 2010

@author: karmel
'''
from glasslab.glassatlas.datatypes.transcript import GlassTranscriptSource,\
    GlassTranscriptSequence, GlassTranscriptNonCoding,\
    GlassTranscriptConserved, GlassTranscriptPatterned,\
    GlassTranscriptNucleotides, GlassTranscriptSourcePrep, GlassTranscriptDuped,\
    GlassTranscriptInfrastructure
from glasslab.config import current_settings
from glasslab.atlasviewer.shared.admin import make_all_fields_readonly,\
    ReadOnlyInline, ReadOnlyAdmin, ReadOnlyInput
import re
from django.utils.safestring import mark_safe
from glasslab.glassatlas.datatypes.transcribed_rna import GlassTranscribedRna,\
    GlassTranscribedRnaSource
from django.db.models.aggregates import Sum
from glasslab.glassatlas.datatypes.feature import PeakFeature
from django.contrib import admin
from glasslab.glassatlas.datatypes.label import GlassTranscriptLabel

class NucleotideSequenceInput(ReadOnlyInput):
    '''
    Subclassed to add custom formatting.
    '''
    start_codons = [['ATG'],['TAC']]
    stop_codons = [['TAA','TAG','TGA'],['TTA','CTA','TCA']]
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        return mark_safe(self.value_for_display(value))
    
    def value_for_display(self, value):
        if value is None or value is '': return '&nbsp;'
        # Create the antisense string
        antisense = value.replace('A','t').replace('T','a').replace('G','c').replace('C','g').upper()[::1]
        # Look at each Reading Frame, starting from the 0th, 1st, and 2nd nucleotide
        display_vals = []
        for strand, sequence in enumerate((value, antisense)):
            all_codons = [[],[],[]]
            stop_codons = [[],[],[]]
            start_codons = [[],[],[]]
            max_orf = (0, 0)
            for offset in xrange(0,3):
                current = sequence[offset:]
                # Split into codons, omitting any leftovers (less than three bases) at the end
                codons = [current[start:start+3] for start in xrange(0,len(current),3) if start + 3 <= len(current)]
                all_codons[offset] = codons
                current_orf = []
                for i, codon in enumerate(codons):
                    if codon in self.start_codons[strand]:
                        start_codons[offset].append(i)
                    if codon in self.stop_codons[strand]:
                        if len(current_orf) > max_orf[1]:
                            max_orf = (offset, len(current_orf)) 
                        stop_codons[offset].append(i)
                        current_orf = []
                    else: current_orf.append(codon)
            # For the max orf, insert spans to show coloring and reassemble
            chosen_codons = all_codons[max_orf[0]]
            for i in stop_codons[max_orf[0]]:
                chosen_codons[i] = '<span class="stop-codon">' + chosen_codons[i] + '</span>' 
            for i in start_codons[max_orf[0]]:
                chosen_codons[i] = '<span class="start-codon">' + chosen_codons[i] + '</span>'
            # Add in line breaks to force wrapping
            step = 45 
            for i in xrange(step,len(chosen_codons),step):
                chosen_codons[i] = '<br />' + chosen_codons[i]
            
            # Join, adding in beginning and end pieces
            end_piece = -((len(sequence) - max_orf[0]) % 3)
            final = sequence[:max_orf[0]] + ''.join(chosen_codons) + (end_piece and sequence[end_piece:] or '')
            
            display_vals.append((max_orf[0],final))
        
        display = '<div class="sense-sequence"><strong>Max ORF starting with nucleotide %d:</strong><br />%s</div>' % display_vals[0]
        display += '<div class="antisense-sequence"><strong>Max ORF starting with nucleotide %d:</strong><br />%s</div>' % display_vals[1]
        
        # And add a key at the end
        key = '<br /><br />'
        for codon_type in ('stop','start'):
            key += '<span class="%s-codon antisense-%s-codon">%s codon</span>&nbsp;&nbsp;&nbsp;&nbsp;' % (
                                                            codon_type,
                                                            codon_type,
                                                            codon_type.replace('-',' '))
        return display + key
    
    def wrap_codon(self, original, value, codons, css_class):
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

class GlassTranscriptSourcePrepInline(ReadOnlyInline):
    model = GlassTranscriptSourcePrep
    readonly_fields = make_all_fields_readonly(model)

class GlassTranscribedRnaInline(ReadOnlyInline):
    model = GlassTranscribedRna
    readonly_fields = make_all_fields_readonly(model)
    ordering = ['chromosome__id','start_end']
    
    def queryset(self, request):
        qs = super(GlassTranscribedRnaInline, self).queryset(request)
        qs = qs.annotate(tags=Sum('glasstranscribedrnasource__tag_count')).filter(tags__gt=1)
        return qs

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
class GlassTranscriptDupedInline(ReadOnlyInline):
    model = GlassTranscriptDuped
    readonly_fields = make_all_fields_readonly(model)
class GlassTranscriptInfrastructureInline(ReadOnlyInline):
    model = GlassTranscriptInfrastructure
    readonly_fields = make_all_fields_readonly(model)

class PeakFeatureInline(ReadOnlyInline):
    model = PeakFeature
    readonly_fields = make_all_fields_readonly(model)

class GlassTranscriptLabelInline(admin.TabularInline):
    extra       = 1
    ordering    = ('manual','probability',)
    model       = GlassTranscriptLabel
    readonly_fields = ('chromosome','strand','start_end','probability')
    
class TranscriptBase(ReadOnlyAdmin):
    ordering        = ('chromosome','transcription_start')
    search_fields   = ['transcription_start','transcription_end',]
    
    def transcript_length(self, obj):
        return obj.transcription_end - obj.transcription_start + 1
    transcript_length.short_description = 'Length'
    
    def ucsc_browser_link(self, obj):
        all_tracks_file = 'all_tracks.txt'
        all_link = self._ucsc_browser_link(obj, all_tracks_file, 'All')
        return all_link
                                       
    def _ucsc_browser_link(self, obj, session_file, text): 
                           
        return '<a href="http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&amp;position=%s%%3A+%d-%d' \
                % (current_settings.REFERENCE_GENOME, obj.chromosome.name.strip(), 
                           obj.transcription_start, obj.transcription_end) \
                + '&amp;hgS_doLoadUrl=submit&amp;hgS_loadUrlName=' \
                + obj.ucsc_session_url + session_file \
                + '" target="_blank">View</a>'
                     
    ucsc_browser_link.short_description = 'UCSC Browser' 
    ucsc_browser_link.allow_tags = True 
    
    def truncated_score(self, obj):
        return obj.score is not None and '%.3f' % obj.score or 'None'
    truncated_score.short_description = 'Score' 
    
    def truncated_density(self, obj):
        return obj.density is not None and '%.3f' % obj.density or 'None'
    truncated_density.short_description = 'Density'

class GlassTranscriptAdmin(TranscriptBase):
    list_display    = ('chromosome','transcription_start','transcription_end','strand',
                       'transcript_length', 'truncated_score', 'spliced', 'ucsc_browser_link', 'modified')
    list_filter     = ('chromosome','strand','spliced')
    
    save_on_top     = True
    inlines         = [GlassTranscriptSequenceInline,
                       GlassTranscriptNonCodingInline,
                       GlassTranscriptSourceInline, 
                       GlassTranscribedRnaInline, 
                       GlassTranscriptLabelInline, 
                       ]

class GlassTranscriptPrepAdmin(TranscriptBase):
    list_display    = ('chromosome','transcription_start','transcription_end','strand',
                       'transcript_length', 'ucsc_browser_link')
    list_filter     = ('chromosome','strand')
    inlines         = [GlassTranscriptSourcePrepInline, 
                       ]
    
class GlassTranscribedRnaSourceInline(ReadOnlyInline):
    model = GlassTranscribedRnaSource   
    readonly_fields = make_all_fields_readonly(model)
    
class GlassTranscribedRnaAdmin(TranscriptBase):
    list_display    = ('chromosome','transcription_start','transcription_end','strand',
                       'transcript_length', 'score','glass_transcript_link','ucsc_browser_link')
    list_filter     = ('chromosome','strand',)
    
    def glass_transcript_link(self, obj):
        if not obj.glass_transcript: return ''
        return '<a href="/admin/Transcription_%s/glasstranscript%s/%d" target="_blank">%s</a>'\
                            % (obj.cell_base.cell_type, obj.cell_base.cell_type.lower(),
                               obj.glass_transcript.id, str(obj.glass_transcript))
                        
    glass_transcript_link.short_description = 'Glass Transcript' 
    glass_transcript_link.allow_tags = True 
    
class PeakFeatureAdmin(ReadOnlyAdmin):
    list_display    = ('glass_transcript_link','relationship','peak_type')
    list_filter     = ('peak_type',)
    
    def glass_transcript_link(self, obj):
        if not obj.glass_transcript: return ''
        return '<a href="/admin/Transcription_%s/glasstranscript%s/%d" target="_blank">%s</a>'\
                            % (obj.cell_base.cell_type, obj.cell_base.cell_type.lower(),
                               obj.glass_transcript.id, str(obj.glass_transcript))
    glass_transcript_link.short_description = 'Glass Transcript' 
    glass_transcript_link.allow_tags = True 
    
    