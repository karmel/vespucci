'''
Created on Feb 23, 2011

@author: karmel
'''
import sys
from glasslab.glassatlas.sql.transcripts_from_tags_functions import sql as transcript_function_sql
from glasslab.glassatlas.sql.transcripts_from_prep_functions import sql as transcript_from_prep_function_sql
from glasslab.glassatlas.sql.glassatlas_table_generator import GlassAtlasTableGenerator
from glasslab.config import current_settings


if __name__ == '__main__':
    genome = len(sys.argv) > 1 and sys.argv[1] or current_settings.GENOME
    cell_type = len(sys.argv) > 2 and sys.argv[2] or current_settings.CELL_TYPE
    subset = len(sys.argv) > 3 and sys.argv[3] or False
    
    generator = GlassAtlasTableGenerator(genome=genome, cell_type=cell_type)
    if subset == 'final':
        print generator.final_set()
        print transcript_from_prep_function_sql(genome, cell_type)
    else: 
        print generator.all_sql()
        print transcript_function_sql(genome, cell_type)
        print transcript_from_prep_function_sql(genome, cell_type)
