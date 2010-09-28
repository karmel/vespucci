#!/bin/bash
'''
Created on Sep 24, 2010

@author: karmel

A script capable of reading in a fastq file, mapping with bowtie,
finding peaks with MACs, and annotating peaks.

Run from the command line like so:
python annotate_peaks.py <source.fastq> <output_dir>

'''
import os
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
import subprocess
import traceback
from datetime import datetime
from random import randint
from glasslab.sequencing.datatypes.peak import CurrentPeak
from glasslab.utils.parsing.delimited import DelimitedFileParser

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
               make_option('--delete_tables',action='store_true', dest='delete_tables', default=False, 
                           help='Delete peak tables after run.'),
               make_option('--skip_bowtie',action='store_true', dest='skip_bowtie', default=False, 
                           help='Skip bowtie; presume MACS uses input file directly.'),
               make_option('--skip_macs',action='store_true', dest='skip_macs', default=False, 
                           help='Skip MACS; presume peak annotation uses input file directly.'),
               ]
    
def check_input(options):
    '''
    Check that required arguments and directories are in place.
    '''
    if not options.file_path:
        raise Exception('Please make sure you have supplied an input FASTQ file and an output directory.')
    if not os.path.exists(options.file_path):
        raise Exception('Sorry, but the specified input file cannot be found: %s' % os.path.realpath(options.file_path))
    
    if not os.path.exists(options.output_dir):
        os.mkdir(options.output_dir)
        print 'Creating output directory %s' % options.output_dir
    
    # Get a file name prefix for use with generated files, using FASTQ as base
    file_name = options.project_name or '.'.join(os.path.basename(options.file_path).split('.')[:-1])
    
    return file_name

def call_bowtie(options, file_name):
    bowtie_output = file_name + '_bowtie.map'
    bowtie_file_path = os.path.join(options.output_dir, bowtie_output)
    bowtie_command = 'bowtie %s %s %s' % (options.genome, options.file_path, bowtie_file_path)
    try: subprocess.check_call(bowtie_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to process FASTQ file with bowtie. Traceback:\n%s'
                                % traceback.format_exc())
    return bowtie_file_path

def call_macs(options, file_name, bowtie_file_path):
    # Note that MACS does not allow output file specification; cd inline to force output into directory
    macs_command = 'cd %s && macs -t %s -n %s -g %s -f BOWTIE' % (options.output_dir,
                                                                  bowtie_file_path, file_name, 
                                                                  'hs' and options.genome[:2] == 'hg' or 'mm')
    if options.control: macs_command += ' -c %s' & options.control
    
    try: subprocess.check_call(macs_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to process bowtie file with MACS. Traceback:\n%s'
                                % traceback.format_exc())
    return os.path.join(options.output_dir, '%s_peaks.xls' % file_name)

def import_peaks(options, file_name, macs_file_path):
    '''
    Given a MACS peak file, save a temp table and store peak data.
    '''
    table_name = '%s_%s_%s' % (file_name.replace(' ','_'), 
                            datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                            str(randint(0,999999)))
    
    CurrentPeak.create_table(table_name)
    data = DelimitedFileParser(macs_file_path).get_array()
    for row in data:
        if row[0] == 'chr': continue
        peak = CurrentPeak.init_from_macs_row(row)
        peak.save()
    
    
if __name__ == '__main__':
    run_from_command_line = True # Useful for debugging in Eclipse
    
    parser = FastqOptionParser()
    options, args = parser.parse_args()
    
    # Allow for easy running from Eclipse
    if not run_from_command_line:
        options.file_path = ''
        options.output_dir = ''
    
    file_name = check_input(options)
    
    if not options.skip_bowtie:
        print 'Processing FASTQ file using bowtie.'
        bowtie_file_path = call_bowtie(options, file_name)
    else:
        print 'Skipping bowtie.'
        bowtie_file_path = options.file_path
    
    if not options.skip_macs:
        print 'Processing bowtie file using MACS'
        macs_file_path = call_macs(options, file_name, bowtie_file_path)
    else:
        print 'Skipping macs.'
        macs_file_path = bowtie_file_path
    
    import_peaks(options, file_name, macs_file_path)