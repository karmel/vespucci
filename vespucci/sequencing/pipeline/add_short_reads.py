'''
Created on Jan 7, 2011

@author: karmel
'''
from datetime import datetime
import os

from django.db import utils

from vespucci.config import current_settings
from vespucci.utils.database import execute_query


def _print(string):
    print(
        '{}: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), string))


def check_input(options):
    '''
    Check that required arguments and directories are in place.
    '''
    if not options.file_name and not getattr(options, 'prep_table', None) \
            and not getattr(options, 'skip_tag_table', None):
        raise Exception('Please make sure you have supplied an input file.')

    if options.file_name and not os.path.exists(options.file_name):
        raise Exception('Sorry, but the specified input file cannot be found: '
                        + os.path.realpath(options.file_name))

    if getattr(options, 'output_dir', None) \
            and not os.path.exists(options.output_dir):
        os.mkdir(options.output_dir)
        _print('Creating output directory ' + options.output_dir)

    if not options.schema_name:
        options.schema_name = current_settings.CURRENT_SCHEMA
    else:
        current_settings.CURRENT_SCHEMA = options.schema_name

    # Get a file name prefix for use with generated files,
    # using input file as base
    generated_name = '.'.join(
        os.path.basename(options.file_name or '').split('.')[:-1])
    file_name = options.project_name or generated_name

    return file_name


def create_schema():
    try:
        execute_query("""
                        CREATE SCHEMA "{0}"; 
                        GRANT Create,Usage ON SCHEMA "{0}" TO  "{1}";
                        """.format(current_settings.CURRENT_SCHEMA,
                                   current_settings.DATABASES['default']['USER']))
    except utils.DatabaseError:
        _print('Schema already created.')
