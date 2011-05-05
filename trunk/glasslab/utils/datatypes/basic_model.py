'''
Created on Nov 5, 2010

@author: karmel
'''
from django.db import models
from glasslab.config import current_settings
from psycopg2.extensions import AsIs

class GlassModel(models.Model):
    class Meta: abstract = True
     
    def get_absolute_url(self):
        return '/admin/%s/%s/%d/' % (self._meta.app_label, 
                                     self.__class__.__name__.lower(),
                                     self.id)
    
class DynamicTable(GlassModel):
    '''
    Dynamically named table.
    '''
    name = None
    table_created = None
    
    class Meta: abstract = True
    
    @classmethod
    def set_table_name(cls, table_name):
        '''
        Set table name for class, incorporating into schema specification.
        '''
        cls._meta.db_table = '%s"."%s' % (current_settings.CURRENT_SCHEMA, table_name)
        cls.name = table_name 

class BoxField(models.Field):
    '''
    Field for the PostgreSQL type box.
    '''
    def from_db_val_to_ints(self, value):
        # Comes in as '((1234,0),(40596,0))' from DB
        try: 
            values = value.strip('(').strip(')').split(',')
            l = []
            for value in values:
                l = l + map(lambda x: float(x.strip('(').strip(')')), value.split(','))
            return l
        except Exception: return value
        
    def get_prep_value(self, value):
        if not value:
            return None
        try: return AsIs('public.make_box(%d,%d,%d,%d)' % tuple(value))
        except TypeError:
            # The value is a string from the DB
            return AsIs('public.make_box(%d,%d,%d,%d)' % tuple(self.from_db_val_to_ints(value)))
        
class CubeField(models.Field):
    '''
    Field for the PostgreSQL type cube (public.cube in the current DB).
    '''
    def from_db_val_to_ints(self, value):
        # Comes in as '(1234),(40596)' from DB
        try: return map(lambda x: int(x.strip('(').strip(')')), value.split(','))
        except Exception: return value
        
        
    def get_prep_value(self, value):
        if value is None:
            return None
        try: return AsIs('public.cube(%d,%d)' % tuple(value))
        except TypeError:
            # The value is a string from the DB
            return AsIs('public.cube(%d,%d)' % tuple(self.from_db_val_to_ints(value)))