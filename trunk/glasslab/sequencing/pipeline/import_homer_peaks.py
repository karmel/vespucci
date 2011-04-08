'''
Created on Apr 7, 2011

@author: karmel
'''
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
from glasslab.sequencing.pipeline.annotate_base import check_input,\
    create_schema
from glasslab.sequencing.datatypes.peak import HomerPeak
from glasslab.utils.parsing.delimited import DelimitedFileParser

class HomerTagsOptionParser(GlassOptionParser):
    options = [
               make_option('-f', '--file_path',action='store', type='string', dest='file_path', 
                           help='Path to Homer output file for processing.'),
               make_option('-g', '--genome',action='store', type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm8, mm8r, mm9, hg18, hg18r'),
               make_option('--project_name',action='store', type='string', dest='project_name',  
                           help='Optional name to be used as file prefix for created files.'),
            
               make_option('--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
            ]


def import_peaks(file_name, peaks_file_path):
    '''
    Given a Homer peak file, store peak data.
    
    NOTE: Homer peak file should be converted into a CSV file first!
    
    '''
    HomerPeak.create_table(file_name)
    
    data = DelimitedFileParser(peaks_file_path).get_array(strip=True)
    for row in data:
        if not row[0].strip() or row[0].strip().find('Cluster') >= 0:
            continue
        peak = HomerPeak.init_from_homer_row(row)
        peak.save()
    
    HomerPeak.add_indices()
    
if __name__ == '__main__': 
    run_from_command_line = True # Useful for debugging in Eclipse
    
    parser = HomerTagsOptionParser()
    options, args = parser.parse_args()
    
    file_name = check_input(options)
    
    create_schema()
    import_peaks(file_name, options.file_path)
    