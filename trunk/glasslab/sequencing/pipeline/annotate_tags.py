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
from glasslab.sequencing.datatypes.tag import GlassTag, GlassTagSequence,\
    GlassTagNonCoding, GlassTagPatterned, GlassTagConserved
from multiprocessing import Pool
from glasslab.config import current_settings
import shutil
from glasslab.config.django_settings import DATABASES
from django.db import utils
from datetime import datetime

class FastqOptionParser(GlassOptionParser):
    options = [
               make_option('-f', '--file_path',action='store', type='string', dest='file_path', 
                           help='Path to FASTQ file for processing.'),
               make_option('-o', '--output_dir',action='store', type='string', dest='output_dir'),
               make_option('-c', '--control',action='store', type='string', dest='control',
                           help='BOWTIE file path to be used for MACS peak finding controls.'),
               make_option('-g', '--genome',action='store', type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm8, mm8r, mm9, hg18, hg18r'),
               make_option('--project_name',action='store', type='string', dest='project_name',  
                           help='Optional name to be used as file prefix for created files.'),
               
               make_option('--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
               
               make_option('--skip_bowtie',action='store_true', dest='skip_bowtie', default=False, 
                           help='Skip bowtie; presume MACS uses input file directly.'),
               make_option('--bowtie_table',action='store', dest='bowtie_table',
                           help='Skip transferring bowtie tags to table; bowtie tag table will be used directly.'),
               make_option('--tag_table',action='store', dest='tag_table',
                           help='Skip translating bowtie tags to Glass tags; tag table will be used directly.'),
               make_option('--do_sequences',action='store_true', dest='do_sequences', default=False, 
                           help='Associate tags with sequence transcriptions regions.'),
               make_option('--do_non_coding',action='store_true', dest='do_non_coding', default=False, 
                           help='Associate tags with non coding transcriptions regions.'),
               make_option('--do_patterned',action='store_true', dest='do_patterned', default=False, 
                           help='Associate tags with patterned transcriptions regions (i.e., repeats).'),
               make_option('--do_conserved',action='store_true', dest='do_conserved', default=False, 
                           help='Associate tags with conserved transcriptions regions (according to phastCons score).'),
               
               make_option('--go',action='store_true', dest='go', default=True,
                           help='Run and output gene ontological analysis.'),
               make_option('--goseq',action='store_true', dest='goseq', default=False,
                           help='Run and output ontological analysis using the GOSeq R library.'),
               ]

def _print(string):
    print '%s: %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), string)
    
def check_input(options):
    '''
    Check that required arguments and directories are in place.
    '''
    if not options.file_path and not options.tag_table and not options.bowtie_table:
        raise Exception('Please make sure you have supplied an input file.')
    if options.file_path and not os.path.exists(options.file_path):
        raise Exception('Sorry, but the specified input file cannot be found: %s' % os.path.realpath(options.file_path))
    
    if options.output_dir and not os.path.exists(options.output_dir):
        os.mkdir(options.output_dir)
        _print('Creating output directory %s' % options.output_dir)
    
    if not options.schema_name: 
        options.schema_name = options.project_name or current_settings.CURRENT_SCHEMA
    current_settings.CURRENT_SCHEMA = options.schema_name
    
    # Get a file name prefix for use with generated files, using FASTQ as base
    file_name = options.project_name or '.'.join(os.path.basename(options.file_path).split('.')[:-1])
    
    return file_name

def call_bowtie(options, file_name):
    # Note that the tag_id, quality score, valid alingments, and mismatches are omitted from the output
    bowtie_output = file_name + '_bowtie.map'
    bowtie_file_path = os.path.join(options.output_dir, bowtie_output)
    
    bowtie_stats = file_name + '_bowtie_stats_summary.txt'
    bowtie_stats_file = open(os.path.join(options.output_dir, bowtie_stats),'w')
    
    bowtie_command = 'bowtie %s %s %s --suppress 1,6,7,8' % (options.genome, options.file_path, bowtie_file_path)
    try: subprocess.check_call(bowtie_command, shell=True, stdout=bowtie_stats_file)
    except Exception:
        raise Exception('Exception encountered while trying to process FASTQ file with bowtie. Traceback:\n%s'
                                % traceback.format_exc())
    return bowtie_file_path

def create_schema():
    try:
        connection.close()
        cursor = connection.cursor()
        cursor.execute("""
                        CREATE SCHEMA "%s"; 
                        GRANT Create,Usage ON SCHEMA "%s" TO  "%s";
                        """ % (current_settings.CURRENT_SCHEMA,
                                current_settings.CURRENT_SCHEMA,
                                DATABASES['default']['USER']))
        transaction.commit_unless_managed()
    except utils.DatabaseError:
        _print('Schema already created.')
    
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
    step_size = len(file_names)//processes
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
    GlassTag.add_record_of_tags()
    
def add_indices():
    # Execute after all the ends have been calculated,
    # as otherwise the insertion of ends takes far too long.
    GlassTag.add_indices()
    
def associate_sequences(options, file_name):
    #GlassTagSequence.set_table_name('tag_sequence_' + file_name)
    GlassTagSequence.create_table(file_name)
    GlassTagSequence.insert_matching_tags()
    GlassTagSequence.add_indices()
    _print('Updating start sites.')
    GlassTagSequence.update_start_site_tags()
    _print('Updating exons.')
    GlassTagSequence.update_exon_tags()
    
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
    
    
    if not options.skip_bowtie and not options.tag_table and not options.bowtie_table:
        _print('Processing FASTQ file using bowtie.')
        bowtie_file_path = call_bowtie(options, file_name)
    else:
        _print('Skipping bowtie.')
        bowtie_file_path = options.file_path
    
    if not options.bowtie_table and not options.tag_table:
        _print('Creating schema if necessary.')
        create_schema()
        _print('Uploading bowtie file into table.')
        bowtie_split_dir = split_bowtie_file(options, file_name, bowtie_file_path)
        upload_bowtie_files(options, file_name, bowtie_split_dir)
    else:
        _print('Skipping upload of bowtie rows into table.')
        GlassTag.set_bowtie_table(options.bowtie_table)
    
    if not options.tag_table:
        _print('Translating bowtie columns to integers.')
        translate_bowtie_columns(file_name)
        _print('Adding indices.')
        add_indices()
    else:
        _print('Skipping translation of bowtie columns to integers')
        GlassTag.set_table_name(options.tag_table)
    
    
    if options.do_sequences:
        _print('Associating tags with sequences.')
        associate_sequences(options, file_name)
    if options.do_non_coding:
        _print('Associating tags with non coding regions.')
        associate_region_table(options, file_name, GlassTagNonCoding)    
    if options.do_patterned:
        _print('Associating tags with patterned regions.')
        associate_region_table(options, file_name, GlassTagPatterned)
    if options.do_conserved:
        _print('Associating tags with conserved regions.')
        associate_region_table(options, file_name, GlassTagConserved)
