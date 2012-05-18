'''
Created on Feb 23, 2011

@author: karmel
'''

genome = 'mm9'
cell_type='thiomac'
def sql(genome, cell_type, subset=False):
    s= """
CREATE SCHEMA "glass_atlas_{0}_{1}_staging" AUTHORIZATION "postgres";

GRANT Create,Usage ON SCHEMA "glass_atlas_{0}_{1}_staging" TO  "glass";
GRANT Usage ON SCHEMA "glass_atlas_{0}_{1}_staging" TO  "glass_read_only";"""

    if subset != 'final':
        s += """
CREATE SCHEMA "glass_atlas_{0}_{1}_prep" AUTHORIZATION "postgres";

GRANT Create,Usage ON SCHEMA "glass_atlas_{0}_{1}_prep" TO  "glass";
GRANT Usage ON SCHEMA "glass_atlas_{0}_{1}_prep" TO  "glass_read_only";


""" 
    return s.format(genome, cell_type)

if __name__ == '__main__':
    print sql(genome, cell_type)
