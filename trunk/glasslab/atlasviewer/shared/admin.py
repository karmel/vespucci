'''
Created on Nov 10, 2010

@author: karmel

Convenience functions and parent classes for Admins.
'''
from django.contrib import admin
from django.db import models
from django.forms.widgets import Input, Select
from django.utils.encoding import force_unicode
from django.forms.util import flatatt
from django.utils.safestring import mark_safe
import itertools

def make_all_fields_readonly(model, include_help_text=False):
    return [f.name for f in model._meta.fields 
                if f.name not in ('id','modified','created') and 
                (not include_help_text or not f.help_text)]

class ReadOnlyInput(Input):
    '''
    Force non-editable display.
    '''
    input_type = 'hidden'
    
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))
        return mark_safe(u'<input%s />%s' % (flatatt(final_attrs), self.value_for_display(value)))
    
    def value_for_display(self, value):
        if value is None or value is '': return '&nbsp;' 
        return value
    
class BooleanReadOnlyInput(ReadOnlyInput):
    def value_for_display(self, value):
        if value is False or value is 0:
            return '<img src="/media/img/admin/icon-no.gif" alt="False" />'
        elif value is True or value is 1:
            return '<img src="/media/img/admin/icon-yes.gif" alt="True" />'
        else:
            return '<img src="/media/img/admin/icon-unknown.gif" alt="Null" />'

class ReadOnlySelect(Select, ReadOnlyInput):
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))
        label = self.value_for_display(value, choices)
        final_attrs['title'] = force_unicode(self._format_value(label.strip()))
        return mark_safe(u'<input%s />%s' % (flatatt(final_attrs), label))
    
    def value_for_display(self, value, choices):
        for option_value, option_label in itertools.chain(self.choices, choices):
            if option_value == value: return option_label
        return value
        
class ReadOnlyInline(admin.TabularInline):
    extra = 0
    max_num = 0
    can_delete = False
    
class ReadOnlyAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.BooleanField: {'widget': BooleanReadOnlyInput },
        models.NullBooleanField: {'widget': BooleanReadOnlyInput },
        models.ForeignKey: {'widget': ReadOnlySelect },
        models.CharField: {'widget': ReadOnlyInput },
        models.IntegerField: {'widget': ReadOnlyInput },
        models.DecimalField: {'widget': ReadOnlyInput },
        models.FloatField: {'widget': ReadOnlyInput },
        models.Field: {'widget': ReadOnlyInput },
    }