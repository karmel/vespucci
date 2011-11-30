'''
Created on Nov 8, 2010

@author: karmel
'''
from django.contrib import admin
from glasslab.utils.datatypes.genetics import InbredStrain, \
    InbredVariant, InbredStrainVariation
from glasslab.atlasviewer.shared.admin import ReadOnlyInline,\
    make_all_fields_readonly, ReadOnlyAdmin


class InbredStrainVariationInline(ReadOnlyInline):
    model = InbredStrainVariation
    readonly_fields = make_all_fields_readonly(model)
    
class InbredStrainAdmin(ReadOnlyAdmin):
    list_display    = ('id','name', 'long_name')
    ordering        = ('id',)
    search_fields   = ('name', 'long_name')

class InbredVariantAdmin(ReadOnlyAdmin):
    list_display    = ('type','chromosome','start','end','reference','ucsc_browser_link')
    ordering        = ('chromosome','start')
    search_fields   = ('start','end','reference')
    list_filter     = ('type','chromosome',)
    
    inlines         = [InbredStrainVariationInline,]
    
    def ucsc_browser_link(self, obj):
        return '<a href="http://genome.ucsc.edu/cgi-bin/hgTracks?position=%s%%3A+%d-%d" target="_blank">View</a>' \
                        % (obj.chromosome.name.strip(), 
                           obj.start - 100, 
                           obj.end + 100)

    ucsc_browser_link.short_description = 'UCSC Browser' 
    ucsc_browser_link.allow_tags = True 
    
class InbredStrainVariationAdmin(ReadOnlyAdmin):
    list_display    = ('inbred_strain','inbred_variant','alternate','ucsc_browser_link')
    ordering        = ('chromosome','inbred_variant__start')
    search_fields   = ('reference','inbred_strain__name','inbred_variant__start','inbred_variant__end')
    list_filter     = ('inbred_strain','inbred_variant__type','chromosome')
    
    def ucsc_browser_link(self, obj):
        return '<a href="http://genome.ucsc.edu/cgi-bin/hgTracks?position=%s%%3A+%d-%d" target="_blank">View</a>' \
                        % (obj.chromosome.name.strip(), 
                           obj.inbred_variant.start - 100, 
                           obj.inbred_variant.end + 100)

    ucsc_browser_link.short_description = 'UCSC Browser' 
    ucsc_browser_link.allow_tags = True 

admin.site.register(InbredStrain, InbredStrainAdmin)
admin.site.register(InbredVariant, InbredVariantAdmin)
admin.site.register(InbredStrainVariation, InbredStrainVariationAdmin)
