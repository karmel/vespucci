'''
Created on Sep 24, 2010

@author: karmel

This module serves as a singleton settings object, for settings that
should be set on a run-wide basis.
'''
import os

#####################################
# Genomes
#####################################
GENOME_CHOICES = {'mm9': {'name':'Mus musculus', 
                          'chromosomes': range(1,23)},
                  'dm3': {'name':'Drosophila melanogaster', 
                          'chromosomes': range(1,15)},
                  'hg19': {'name':'Homo sapiens', 
                          'chromosomes': range(1,26)},
                  }

GENOME = 'mm9'


CELL_TYPE = 'Default'

STAGING = '' # Set to the appropriate suffix during DB staging.
STAGING_SUFFIX = '_staging'

MAX_EDGE = 500 # Max edge length in 2D between two proto-transcripts
DENSITY_MULTIPLIER = 10000 # Scaling factor on density-- bps worth of tags to consider

#####################################
# Databases
#####################################
# Password should be stored in directory above main package,
# in a file called .database_password
current_dir = os.path.dirname(__file__)
password = file(os.path.join(current_dir, '../../.database_password')).read()
password = password.strip('\n').strip()
CURRENT_SCHEMA = 'current_projects'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'vespucci',
        'USER': 'vespucci_user',
        'PASSWORD': password,
        'HOST': 'localhost',
        'PORT': '5432',  
    },
    'pgbouncer': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'vespucci',
        'USER': 'vespucci_user',
        'PASSWORD': password,
        'HOST': 'localhost',
        'PORT': '6432',  
    },

}
CONNECTION = None

#####################################
# Compute power
#####################################
ALLOWED_PROCESSES = 5
CHR_LISTS = None # Dynamically set during processing

#####################################
# Required for Django; not used
#####################################
SECRET_KEY = 'feg^reh@(rdyue(yfawu0mg532ok^yfl9$1%*ge+ng$1@0gf%x'
