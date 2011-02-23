'''
Created on Sep 24, 2010

@author: karmel

This module serves as a singleton settings object, for settings that
should be set on a run-wide basis.
'''

#####################################
# Genomes
#####################################
GENOME_CHOICES = ['test','mm9']

REFERENCE_GENOME = 'mm9'
TRANSCRIPT_GENOME = 'gap3_100_10' # Separated for easy use of the 'test' DB while keeping reference DB
GENOME = REFERENCE_GENOME

GENOME_ASSEMBLY_PATHS = {'mm9': '/Volumes/Unknowme/kallison/Genomes/mm9/fasta',}

#####################################
# Databases
#####################################
CURRENT_SCHEMA = 'current_projects'
CURRENT_CELL_TYPE = 'ThioMac'

#####################################
# Compute power
#####################################
ALLOWED_PROCESSES = 4
CHR_LISTS = None # Dynamically set during processing
