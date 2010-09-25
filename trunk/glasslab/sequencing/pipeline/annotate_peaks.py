#!/bin/bash
'''
Created on Sep 24, 2010

@author: karmel

A script capable of reading in a fastq file, mapping with bowtie,
finding peaks with MACs, and annotating peaks.

Run from the command line like so:
python annotate_peaks.py <source.fastq> <output_dir>

'''
import sys
import os
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option

class FastqOptionParser(GlassOptionParser):
    options = [
               make_option('-f', '--file_path',action='store', type='string', dest='file_path'),
               make_option('-o', '--output_dir',action='store', type='string', dest='output_dir'),
               make_option('-g', '--genome',action='store', type='string', dest='genome'),
               ]
if __name__ == '__main__':
    run_from_command_line = True # Useful for debugging in Eclipse
    
    if run_from_command_line and len(sys.argv) < 3:
        raise Exception('Please make sure you have supplied an input FASTQ file and an output directory.')
    if not run_from_command_line:
        input = ''
        output_dir = ''
    else:
        input = sys.argv[1]
        output_dir = sys.argv[2]

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
        print 'Creating output directory %s' % output_dir
    
    print 'Processing FASTQ file using bowtie.'