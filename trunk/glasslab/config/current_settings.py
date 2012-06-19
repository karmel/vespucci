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
TRANSCRIPT_GENOME = 'mm9' # Separated for easy use of the 'test' DB while keeping reference DB
GENOME = REFERENCE_GENOME
GENOME_CHROMOSOMES = range(1,23)

STAGING = '' # Set to the appropriate suffix during DB staging.
STAGING_SUFFIX = '_staging'

GENOME_ASSEMBLY_PATHS = {'mm9': '/Volumes/Unknowme/kallison/Genomes/mm9/fasta',}

#####################################
# Databases
#####################################
CURRENT_SCHEMA = 'current_projects'
CURRENT_CELL_TYPE = 'ThioMac'

#####################################
# Compute power
#####################################
ALLOWED_PROCESSES = 6
CHR_LISTS = None # Dynamically set during processing

#####################################
# Compute resources
#####################################
# Used to log in as postgres user. Note that authorized keys must be set up!
PG_ACCESS_CMD = 'ssh postgres@glass.bioinforma.tc' 
PG_HOME = '/Library/PostgreSQL/9.1'
