'''
Created on Jan 6, 2011

@author: karmel
'''
from django.contrib import admin
from glasslab.glassatlas.datatypes.metadata import SequencingRun,\
    SequencingRunAnnotation

class SequencingRunAnnotationInline(admin.TabularInline):
    extra       = 1
    ordering    = ('note',)
    model       = SequencingRunAnnotation
    
class SequencingRunAdmin(admin.ModelAdmin):
    list_display    = ('type', 'cell_type','description', 'source_table', 'total_tags')
    list_filter     = ('type','cell_type')
    ordering        = ('-modified',)
    inlines         = [SequencingRunAnnotationInline]
    
admin.site.register(SequencingRun, SequencingRunAdmin)