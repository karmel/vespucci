'''
Created on Feb 23, 2011

@author: karmel

Generates sql statements for 
'''
from glasslab.config import current_settings

def sql(genome, cell_type, subset=False):
    s= """
CREATE SCHEMA "glass_atlas_{0}_{1}{staging}" AUTHORIZATION "{user}";"""

    if subset != 'final':
        s += """
CREATE SCHEMA "glass_atlas_{0}_{1}_prep" AUTHORIZATION "{user}";


""" 
    return s.format(genome, cell_type, 
                    staging=current_settings.STAGING, 
                    user=current_settings.DATABASES['default']['USER'])