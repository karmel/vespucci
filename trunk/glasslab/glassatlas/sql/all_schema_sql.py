'''
Created on Feb 23, 2011

@author: karmel
'''
import sys
from glasslab.glassatlas.sql.create_schema_sql import sql as schema_sql
from glasslab.glassatlas.sql.generate_transcript_table_sql import sql as transcript_table_sql
from glasslab.glassatlas.sql.generate_transcript_prep_table_sql import sql as prep_table_sql
from glasslab.glassatlas.sql.generate_feature_table_sql import sql as features_table_sql
from glasslab.glassatlas.sql.transcripts_from_tags_functions import sql as transcript_function_sql
from glasslab.glassatlas.sql.transcripts_from_prep_functions import sql as transcript_from_prep_function_sql
from glasslab.glassatlas.sql.features_functions import sql as features_function_sql

def print_all(genome, cell_type='thiomac'):
    print schema_sql(genome, cell_type)
    print prep_table_sql(genome, cell_type)
    print transcript_table_sql(genome, cell_type)
    print features_table_sql(genome, cell_type)
    print transcript_function_sql(genome, cell_type)
    print transcript_from_prep_function_sql(genome, cell_type)
    print features_function_sql(genome, cell_type)

def print_final(genome, cell_type='thiomac'):
    print schema_sql(genome, cell_type, subset='final')
    print transcript_table_sql(genome, cell_type)
    print features_table_sql(genome, cell_type)
    print transcript_from_prep_function_sql(genome, cell_type)
    print features_function_sql(genome, cell_type)
    
    
if __name__ == '__main__':
    genome = len(sys.argv) > 1 and sys.argv[1] or 'gap3_100_10'
    cell_type = len(sys.argv) > 2 and sys.argv[2] or 'thiomac'
    subset = len(sys.argv) > 3 and sys.argv[3] or False
    
    if subset == 'final':
        print_final(genome, cell_type)
    else: print_all(genome, cell_type)
    