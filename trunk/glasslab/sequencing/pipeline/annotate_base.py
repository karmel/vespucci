'''
Created on Jan 7, 2011

@author: karmel
'''
import traceback
import subprocess
from glasslab.config import current_settings
from django.db import utils
from datetime import datetime
import os
from glasslab.config.django_settings import DATABASES
from glasslab.utils.database import execute_query

def _print(string):
    print '%s: %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), string)
    
def check_input(options):
    '''
    Check that required arguments and directories are in place.
    '''
    if not options.file_path and not getattr(options, 'bowtie_table', None) and not getattr(options, 'skip_tag_table', None):
            raise Exception('Please make sure you have supplied an input file.')
        
    if options.file_path and not os.path.exists(options.file_path):
        raise Exception('Sorry, but the specified input file cannot be found: %s' % os.path.realpath(options.file_path))
    
    if getattr(options,'output_dir',None) and not os.path.exists(options.output_dir):
        os.mkdir(options.output_dir)
        _print('Creating output directory %s' % options.output_dir)
    
    if not options.schema_name: 
        options.schema_name = options.project_name or current_settings.CURRENT_SCHEMA
    current_settings.CURRENT_SCHEMA = options.schema_name
    
    if options.genome: current_settings.GENOME = options.genome
    
    # Get a file name prefix for use with generated files, using FASTQ as base
    file_name = options.project_name or '.'.join(os.path.basename(options.file_path).split('.')[:-1])
    
    return file_name

def call_bowtie(options, file_name, suppress_columns=False):
    # Note that the tag_id, quality score, valid alingments, and mismatches are omitted from the output
    bowtie_output = file_name + '_bowtie.map'
    bowtie_file_path = os.path.join(options.output_dir, bowtie_output)
    
    bowtie_stats = file_name + '_bowtie_stats_summary.txt'
    bowtie_stats_file = open(os.path.join(options.output_dir, bowtie_stats),'w')
    
    supress_string = suppress_columns and '--suppress 1,6,7,8' or ''
    bowtie_command = 'bowtie -m 3 %s %s %s %s' % (current_settings.GENOME, options.file_path, 
                                             bowtie_file_path, supress_string)
    try: subprocess.check_call(bowtie_command, shell=True, stdout=bowtie_stats_file, stderr=subprocess.STDOUT)
    except Exception:
        raise Exception('Exception encountered while trying to process FASTQ file with bowtie. Traceback:\n%s'
                                % traceback.format_exc())
    bowtie_stats_file.close()
    return bowtie_file_path

def create_schema():
    try:
        execute_query("""
                        CREATE SCHEMA "%s"; 
                        GRANT Create,Usage ON SCHEMA "%s" TO  "%s";
                        """ % (current_settings.CURRENT_SCHEMA,
                                current_settings.CURRENT_SCHEMA,
                                DATABASES['default']['USER']))
    except utils.DatabaseError:
        _print('Schema already created.')