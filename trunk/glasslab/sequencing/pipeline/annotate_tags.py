#!/bin/bash
'''
Created on Oct 18, 2010

@author: karmel

A script capable of reading in a fastq file, mapping with bowtie,
loading tags into a table, and associating with the appropriate transcription regions.

Run from the command line like so:
python annotate_peaks.py -f <source.fastq> -o <output_dir> --project_name=my_project

'''
from __future__ import division
import os
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
import subprocess
import traceback

from django.db import connection, transaction
from glasslab.sequencing.datatypes.tag import GlassTag
from multiprocessing import Pool
from glasslab.config import current_settings
import shutil
from glasslab.sequencing.pipeline.annotate_base import check_input, _print,\
    call_bowtie, create_schema, trim_sequences, clean_bowtie_file
from glasslab.utils.database import execute_query_without_transaction

class FastqOptionParser(GlassOptionParser):
    options = [
               make_option('-f', '--file_path',action='store', type='string', dest='file_path', 
                           help='Path to FASTQ file for processing.'),
               make_option('-o', '--output_dir',action='store', type='string', dest='output_dir'),
               make_option('-g', '--genome',action='store', type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm8, mm8r, mm9, hg18, hg18r'),
               make_option('--project_name',action='store', type='string', dest='project_name',  
                           help='Optional name to be used as file prefix for created files.'),
               
               make_option('--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
               
               make_option('--clean_bowtie',action='store_true', dest='clean_bowtie', default=False, 
                           help='Clean an already bowtied file of dupes.'),                           
               make_option('--skip_trim',action='store_true', dest='skip_trim', default=False, 
                           help='Trim the sequences of polyA regions before sending to bowtie.'),
                           
               make_option('--skip_bowtie',action='store_true', dest='skip_bowtie', default=False, 
                           help='Skip bowtie; presume MACS uses input file directly.'),
               make_option('--bowtie_table',action='store', dest='bowtie_table',
                           help='Skip transferring bowtie tags to table; bowtie tag table will be used directly.'),
               make_option('--skip_tag_table',action='store_true', dest='skip_tag_table',
                           help='Skip transferring tags to table; tag table will be used directly.'),
               
               ]
    
def split_bowtie_file(options, file_name, bowtie_file_path):
    '''
    Trying to upload a single file all at once into the table often means we lose the DB
    connection. Split the large file here to allow more manageable looping.
    '''
    output_dir = os.path.join(options.output_dir, 'bowtie_split_files')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    output_prefix = os.path.join(output_dir, '%s_' % file_name)
    split_command = 'split -a 4 -l 100000 %s %s' % (bowtie_file_path, output_prefix)
    try: subprocess.check_call(split_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to split bowtie file. Traceback:\n%s'
                                % traceback.format_exc())
    
    return output_dir

def copy_into_table_from_range(bowtie_split_dir, file_names):
    for f_name in file_names:
        _copy_into_table(bowtie_split_dir, f_name)
         
def _copy_into_table(bowtie_split_dir, f_name):
    full_path = os.path.join(bowtie_split_dir,f_name)
    bowtie_file = file(full_path)
    try:
        connection.close()
        cursor = connection.cursor()
        cursor.copy_expert("""COPY "%s" (strand_char, chromosome, "start", sequence_matched)
                                FROM STDIN WITH CSV DELIMITER E'\t'; """ % GlassTag.bowtie_table, bowtie_file)
        transaction.commit_unless_managed()
    except Exception:
        _print('Encountered exception while trying to copy data:\n%s' % traceback.format_exc())
        raise
    
def upload_bowtie_files(options, file_name, bowtie_split_dir):
    GlassTag.create_bowtie_table(file_name)
    
    file_names = os.listdir(bowtie_split_dir)
    processes = current_settings.ALLOWED_PROCESSES
    step_size = max(1,len(file_names)//processes)
    p = Pool(processes) 
    for start in xrange(0,len(file_names),step_size):
        try:
            p.apply_async(copy_into_table_from_range,args=(bowtie_split_dir, file_names[start:(start + step_size)]))
        except Exception:
            raise Exception('Exception encountered while trying to upload bowtie files to tables. Traceback:\n%s'
                                % traceback.format_exc())
    p.close()
    p.join()
    
    connection.close()
    shutil.rmtree(bowtie_split_dir)

def translate_bowtie_columns(file_name):
    '''
    Transfer bowtie tags to indexed, streamlined Glass tags for annotation.
    '''
    #GlassTag.set_table_name('tag_' + file_name)
    GlassTag.create_parent_table(file_name)
    GlassTag.create_partition_tables()
    GlassTag.translate_from_bowtie()
    GlassTag.add_record_of_tags(stats_file=getattr(options,'bowtie_stats_file',None))
    
def add_indices():
    # Execute after all the ends have been calculated,
    # as otherwise the insertion of ends takes far too long.
    GlassTag.add_indices()
    execute_query_without_transaction('VACUUM ANALYZE "%s";' % (GlassTag._meta.db_table))
    GlassTag.set_refseq()
    
def fix_tags(bowtie_file, file_name):
    GlassTag.set_table_name('tag_' + file_name)
    GlassTag.create_partition_tables()
    f = open(bowtie_file)
    for line in f.readlines():
        line = line.strip('\n')
        GlassTag.fix_tags(line.split('\t'))
    
def associate_region_table(options, file_name, table_class):
    table_class.create_table(file_name)
    table_class.insert_matching_tags()
    table_class.add_indices()
    
if __name__ == '__main__':    
    run_from_command_line = True # Useful for debugging in Eclipse
    
    parser = FastqOptionParser()
    options, args = parser.parse_args()

    # Allow for easy running from Eclipse
    if not run_from_command_line:
        options.do_bowtie = False
        options.file_path = '/Volumes/Unknowme/kallison/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/tags/ncor_ko_kla_1h/ncor_ko_kla_1h_bowtie.map'
        options.output_dir = '/Volumes/Unknowme/kallison/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/tags/ncor_ko_kla_1h'
        options.project_name = 'ncor_ko_kla_1h_2'
        
    file_name = check_input(options)
    
    if options.clean_bowtie:
        _print('Cleaning existing bowtie file.')
        bowtie_file_path = clean_bowtie_file(options, file_name)
    elif not options.skip_bowtie and not options.bowtie_table:
        if not options.skip_trim:
            trim_sequences(options, file_name)
            
        _print('Processing FASTQ file using bowtie.')
        bowtie_file_path = call_bowtie(options, file_name, suppress_columns=True)
    else:
        _print('Skipping bowtie.')
        bowtie_file_path = options.file_path
        options.bowtie_stats_file = os.path.join(options.output_dir,'%s_bowtie_stats_summary.txt' % file_name)
    
    if not options.skip_tag_table:
        
        if not options.bowtie_table:
            _print('Creating schema if necessary.')
            create_schema()
            _print('Uploading bowtie file into table.')
            bowtie_split_dir = split_bowtie_file(options, file_name, bowtie_file_path)
            upload_bowtie_files(options, file_name, bowtie_split_dir)
        else:
            _print('Skipping upload of bowtie rows into table.')
            GlassTag.set_bowtie_table(options.bowtie_table)
        
        _print('Translating bowtie columns to integers.')
        translate_bowtie_columns(file_name)
        _print('Adding indices.')
        GlassTag.set_table_name('tag_' + file_name)
        add_indices()
    else:
        _print('Skipping creation of tag table')
        GlassTag.set_table_name('tag_' + file_name)
        GlassTag.set_refseq()
