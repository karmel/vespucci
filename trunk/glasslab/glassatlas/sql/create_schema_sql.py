'''
Created on Feb 23, 2011

@author: karmel
'''

genome = 'mm9'
cell_type='thiomac'
def sql(genome, cell_type):
    return """
CREATE SCHEMA "glass_atlas_%s_%s" AUTHORIZATION "postgres";

GRANT Create,Usage ON SCHEMA "glass_atlas_%s_%s" TO  "glass";
GRANT Usage ON SCHEMA "glass_atlas_%s_%s" TO  "glass_read_only";

CREATE SCHEMA "glass_atlas_%s_%s_prep" AUTHORIZATION "postgres";

GRANT Create,Usage ON SCHEMA "glass_atlas_%s_%s_prep" TO  "glass";
GRANT Usage ON SCHEMA "glass_atlas_%s_%s_prep" TO  "glass_read_only";

CREATE SCHEMA "glass_atlas_%s_%s_rna" AUTHORIZATION "postgres";

GRANT Create,Usage ON SCHEMA "glass_atlas_%s_%s_prep" TO  "glass";
GRANT Usage ON SCHEMA "glass_atlas_%s_%s_prep" TO  "glass_read_only";

""" % tuple([genome, cell_type]*9)

if __name__ == '__main__':
    print sql(genome, cell_type)
