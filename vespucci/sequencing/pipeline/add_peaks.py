#!/bin/bash
'''
Created on Sep 24, 2010

@author: karmel

A script capable of reading in a peak file 
and appropriately denormalizing into DB tables.

Run from the command line.

'''
from vespucci.utils.scripting import VespucciOptionParser
from optparse import make_option
from vespucci.sequencing.datatypes.peak import AtlasPeak
from vespucci.sequencing.pipeline.add_short_reads import check_input, \
    create_schema, _print
from pandas.io.parsers import read_csv

class PeakFileParser(VespucciOptionParser):
    options = [
               make_option('-f', '--file_name', action='store', 
                           type='string', dest='file_name', 
                           help='Path to FASTQ file for processing.'),
               make_option('-g', '--genome', action='store', 
                           type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm9, dm3'),
               make_option('--project_name', action='store', 
                           type='string', dest='project_name',  
                           help='Optional name to be used as file prefix for created files.'),
            
               make_option('--schema_name', action='store', 
                           type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
               
               make_option('--not_homer', action='store', 
                           dest='not_homer', default=False, 
                           help='If the input file is not a HOMER peaks file, what is it? (bed, macs, sicer)'),
                           
               ]
    

def import_peaks(options, file_name, peaks_file_name):
    '''
    Given a  peak file, save a temp table and store peak data.
    '''
    AtlasPeak.create_table(file_name)
    #AtlasPeak.set_table_name('peak_' + file_name)
    
    if not options.not_homer:
        # Find header row
        header_row = None
        f = file(peaks_file_name)
        for i,line in enumerate(f):
            print line[:6]
            if line[:6] == '#PeakID': 
                header_row = i
                break
        if header_row is None: 
            raise Exception('There is no header in this Homer peak file!') 
        data = read_csv(peaks_file_name, sep='\t', header=i, skiprows=i)
    else: data = read_csv(peaks_file_name, sep='\t', header=None)
    
    for _, row in data.iterrows():
        if not options.not_homer:
            peak = AtlasPeak.init_from_homer_row(row)
        else:
            peak = getattr(AtlasPeak, 
                           'init_from_{0}_row'.format(options.not_homer))(row)

        peak.save()

    AtlasPeak.add_indices()
    
    
if __name__ == '__main__': 
    run_from_command_line = True # Useful for debugging in Eclipse
    
    parser = PeakFileParser()
    options, args = parser.parse_args()
    
    
    file_name = check_input(options)
    peaks_file_name = options.file_name
    parser.set_genome(options)
    
    _print('Creating schema if necessary.')
    create_schema()
    _print('Saving peaks to table.')
    import_peaks(options, file_name, peaks_file_name)
