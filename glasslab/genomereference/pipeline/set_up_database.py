'''
Created on Feb 23, 2011

@author: karmel
'''
from glasslab.utils.database import execute_query
from optparse import make_option
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from glasslab.glassatlas.pipeline.base_parser import GlassAtlasParser
from glasslab.genomereference.sql.sql_generator import GenomeResourcesSqlGenerator

class SetUpDatabaseParser(GlassAtlasParser):
    options = [
               make_option('-g', '--genome',action='store', type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm8, mm8r, mm9, hg18, hg18r'),
               make_option('-c', '--cell_type',action='store', type='string', dest='cell_type', 
                           help='Cell type for this run? Options are: %s' % ','.join(CellTypeBase.get_correlations().keys())),
               make_option('--schema_only', action='store_true', dest='schema_only', default=False,
                           help='Only create schema and stop before importing all the data?'),
                ]

if __name__ == '__main__':
    parser = SetUpDatabaseParser()
    options, args = parser.parse_args()
    
    cell_type, cell_base = parser.set_cell(options)
    genome = parser.set_genome(options)
    
    generator = GenomeResourcesSqlGenerator(cell_type=cell_type, genome=genome)
    
    print 'Creating genome resources database schema and tables...'
    q = generator.all_sql()
    execute_query(q)
    if not options.schema_only: 
        q_set = generator.fill_tables_mm9()
        for q in q_set: execute_query(q)
    
    # And cleanup the import tables:
    execute_query(generator.cleanup())