'''
Created on Feb 23, 2011

@author: karmel
'''
from glasslab.config import current_settings

genome = 'mm9'
cell_type='thiomac'
def sql(genome, cell_type, subset=False):
    s= """
CREATE SCHEMA "glass_atlas_{0}_{1}{2}" AUTHORIZATION "{3}";"""

    if subset != 'final':
        s += """
CREATE SCHEMA "glass_atlas_{0}_{1}_prep" AUTHORIZATION "{3}";


""" 
    return s.format(genome, cell_type, 
                    current_settings.STAGING, 
                    current_settings.DATABASES['default']['user'])

if __name__ == '__main__':
    print sql(genome, cell_type)
