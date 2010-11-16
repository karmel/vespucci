'''
Created on Nov 5, 2010

@author: karmel
'''
from django.db import models
from glasslab.config import current_settings
from psycopg2.extensions import AsIs
  
class DynamicTable(models.Model):
    '''
    Dynamically named table.
    '''
    name = None
    table_created = None
    
    schema = current_settings.CURRENT_SCHEMA
    
    class Meta: abstract = True
    
    @classmethod
    def set_table_name(cls, table_name):
        '''
        Set table name for class, incorporating into schema specification.
        '''
        cls._meta.db_table = '%s"."%s' % (cls.schema, table_name)
        cls.name = table_name 

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