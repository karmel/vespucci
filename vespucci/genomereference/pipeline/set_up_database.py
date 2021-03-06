'''
Created on Feb 23, 2011

@author: karmel
'''
from optparse import make_option

from vespucci.config import current_settings
from vespucci.genomereference.sql.sql_generator import GenomeResourcesSqlGenerator
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
        make_option('--schema_only', action='store_true',
                    dest='schema_only', default=False,
                    help='Only create schema and stop before importing all the data?'),
    ]

if __name__ == '__main__':
    django_setup()

    parser = SetUpDatabaseParser()
    options, args = parser.parse_args()

    cell_type, cell_base = parser.set_cell(options)
    genome = parser.set_genome(options)

    generator = GenomeResourcesSqlGenerator(cell_type=cell_type, genome=genome)

    print('Creating genome resources database schema and tables...')
    q = generator.all_sql()
    execute_query(q)
    if not options.schema_only and genome in current_settings.GENOME_CHOICES.keys():
        q_set = generator.fill_tables()
        for q in q_set:
            if q:
                execute_query(q)

    # And cleanup the import tables:
    execute_query(generator.cleanup())
