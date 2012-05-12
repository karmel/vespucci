'''
Created on Feb 23, 2011

@author: karmel
'''

genome = 'mm9'
cell_type='thiomac'
def sql(genome, cell_type, subset=False):
    count = 3
    s= """
CREATE SCHEMA "glass_atlas_%s_%s_staging" AUTHORIZATION "postgres";

GRANT Create,Usage ON SCHEMA "glass_atlas_%s_%s_staging" TO  "glass";
GRANT Usage ON SCHEMA "glass_atlas_%s_%s_staging" TO  "glass_read_only";"""

    if subset != 'final':
        count = 6
        s += """
CREATE SCHEMA "glass_atlas_%s_%s_prep" AUTHORIZATION "postgres";

GRANT Create,Usage ON SCHEMA "glass_atlas_%s_%s_prep" TO  "glass";
GRANT Usage ON SCHEMA "glass_atlas_%s_%s_prep" TO  "glass_read_only";


""" 
    return s % tuple([genome, cell_type]*count)

if __name__ == '__main__':
    print sql(genome, cell_type)
