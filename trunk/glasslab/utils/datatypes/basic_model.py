'''
Created on Nov 5, 2010

@author: karmel
'''
from django.db import models
from glasslab.config import current_settings
  
class DynamicTable(models.Model):
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