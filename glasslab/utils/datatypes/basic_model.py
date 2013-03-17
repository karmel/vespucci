'''
Created on Nov 5, 2010

@author: karmel
'''
from django.db import models
from glasslab.config import current_settings
from psycopg2.extensions import AsIs

class GlassMeta(object):
    '''
    To be used for the Django Meta classes on Glass Models.
    Has methods for getting and setting that pesky db_table name
    dynamically.
    '''
    db_table = ''
    
    db_table_base = ''
    
    @classmethod
    def get_db_table(cls): return cls.db_table
    @classmethod
    def get_db_table_from_base(cls): 
        return cls.db_table_base.format(current_settings.GENOME, current_settings.CELL_TYPE)
    
    @classmethod
    def set_db_table(cls, val): cls.db_table = val
    @classmethod
    def set_db_table_from_base(cls, val): 
        '''
        Expects list of formatting vars.
        '''
        cls.db_table = cls.db_table_base.format(*val)
    
    @classmethod
    def del_db_table(cls): cls.db_table = ''
        
class GlassModel(models.Model):
    schema_base = 'glass_atlas_{0}_{1}'
    
    @classmethod
    def set_db_table(cls):
        cls.schema_name = cls.schema_base.format(current_settings.GENOME, current_settings.CELL_TYPE.lower())
        cls._meta.db_table = cls._meta.db_table.format(current_settings.GENOME, current_settings.CELL_TYPE.lower())
    
    def get_absolute_url(self):
        return '/admin/%s/%s/%d/' % (self._meta.app_label, 
                                     self.__class__.__name__.lower(),
                                     self.id)
    class Meta(GlassMeta): abstract = True

 
class DynamicTable(GlassModel):
    '''
    Dynamically named table.
    '''
    name = None
    table_created = None
    
    class Meta(GlassMeta): abstract = True
    
    @classmethod
    def set_table_name(cls, table_name):
        '''
        Set table name for class, incorporating into schema specification.
        '''
        cls._meta.db_table = '%s"."%s' % (current_settings.CURRENT_SCHEMA, table_name)
        cls.name = table_name 
    
class RangeField(models.Field):
    '''
    Field for the PostgreSQL type range. 
    
    .. warning:: 
        This is not designed to be a full implementation of a Django field.
        This is merely for display convenience, and does not translate
        exclusivity versus inclusivity, datatypes, etc.
    '''
    range_type = 'range'
    def from_db_val_to_ints(self, value):
        # Comes in as '(1234,40596)' from DB
        # Note that we lose
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
        try: return AsIs(self.range_type + '(%d,%d)' % tuple(value))
        except TypeError:
            # The value is a string from the DB
            return AsIs(self.range_type + '(%d,%d)' % tuple(self.from_db_val_to_ints(value)))

class Int8RangeField(RangeField):
    range_type = 'int8range'
    
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