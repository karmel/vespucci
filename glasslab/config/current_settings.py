'''
Created on Sep 24, 2010

@author: karmel

This module serves as a singleton settings object, for settings that
should be set on a run-wide basis.
'''

#####################################
# Genomes
#####################################
GENOME_CHOICES = {'mm9': {'name':'Mus musculus', 'chromosomes': range(1,23)},
                  'dm3': {'name':'Drosophila melanogaster', 'chromosomes': range(1,15)}}

GENOME = 'mm9'


CELL_TYPE = 'Default'

STAGING = '' # Set to the appropriate suffix during DB staging.
STAGING_SUFFIX = '_staging'

MAX_EDGE = 100 # Max edge length in 2D between two proto-transcripts

#####################################
# Databases
#####################################
CURRENT_SCHEMA = 'current_projects'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'glassatlas',
        'USER': 'glassatlas_user',
        'PASSWORD': 'I#found#Waldo',
        'HOST': 'localhost',
        'PORT': '5432',
    },

}

#####################################
# Compute power
#####################################
ALLOWED_PROCESSES = 5
CHR_LISTS = None # Dynamically set during processing

