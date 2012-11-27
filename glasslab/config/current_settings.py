'''
Created on Sep 24, 2010

@author: karmel

This module serves as a singleton settings object, for settings that
should be set on a run-wide basis.
'''
#####################################
# Genomes
#####################################
GENOME_CHOICES = ['mm9']

GENOME = 'mm9'
GENOME_CHROMOSOMES = range(1,23)


CELL_TYPE = 'ThioMac'

STAGING = '' # Set to the appropriate suffix during DB staging.
STAGING_SUFFIX = '_staging'

#####################################
# Databases
#####################################
CURRENT_SCHEMA = 'current_projects'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'glassatlas',
        'USER': 'glassatlas_user',
        'PASSWORD': 'I#found#Waldo.',
        'HOST': 'localhost',
        'PORT': '5432',
    },

}

#####################################
# Compute power
#####################################
ALLOWED_PROCESSES = 5
CHR_LISTS = None # Dynamically set during processing

