'''
Created on Feb 23, 2011

@author: karmel
'''
from optparse import make_option

from vespucci.atlas.sql.sql_generator import AtlasSqlGenerator
from vespucci.utils.database import execute_query
from vespucci.utils.scripting import VespucciOptionParser, django_setup


class SetUpDatabaseParser(VespucciOptionParser):
    options = [
        make_option('-g', '--genome', action='store',
                    type='string', dest='genome', default='mm9',
                    help='Currently supported: mm9, dm3'),
        make_option('-c', '--cell_type', action='store',
                    type='string', dest='cell_type',
                    help='Cell type for this run?'),
        make_option('-f', '--final', action='store_true',
                    dest='final', default=False,
                    help='Generate only the final schema and tables, without the prep schema?'),
        make_option('-p', '--prep', action='store_true',
                    dest='prep', default=False,
                    help='Generate only the prep schema and tables, without the final schema?'),
    ]

if __name__ == '__main__':
    django_setup()

    parser = SetUpDatabaseParser()
    options, args = parser.parse_args()

    genome = parser.set_genome(options)
    cell_type, cell_base = parser.set_cell(options)

    generator = AtlasSqlGenerator(cell_type=cell_type, genome=genome)

    print('Creating database schema and tables...')
    q = (options.final and generator.final_set()) \
        or (options.prep and generator.prep_set()) \
        or generator.all_sql()
    execute_query(q)
