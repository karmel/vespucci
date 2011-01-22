'''
Created on Jan 6, 2011

@author: karmel
'''
from django.contrib import admin
from glasslab.glassatlas.datatypes.metadata import SequencingRun,\
    SequencingRunAnnotation, PeakType

class SequencingRunAnnotationInline(admin.TabularInline):
    extra       = 1
    ordering    = ('note',)
    model       = SequencingRunAnnotation
    
class SequencingRunAdmin(admin.ModelAdmin):
    list_display    = ('type', 'cell_type','description', 'source_table', 'total_tags','percent_mapped')
    list_filter     = ('type','cell_type')
    ordering        = ('-modified',)
    inlines         = [SequencingRunAnnotationInline]

class PeakTypeAdmin(admin.ModelAdmin):
    list_display    = ('type', 'diffuse')
    list_filter     = ('diffuse',)
    ordering        = ('-type',)
    
admin.site.register(SequencingRun, SequencingRunAdmin)
admin.site.register(PeakType, PeakTypeAdmin)