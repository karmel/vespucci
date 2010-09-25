'''
Created on Sep 24, 2010

@author: karmel
'''
from django.db import models
    
#######################################################
# Gene identifiers
#######################################################
class GeneIdentifier(models.Model):
    '''
    Gene identifiers from RefSeq, unique per genome.
    '''
    genome = models.CharField(max_length=10,choices=[(x,x) for x in ('mm9','mm8','mm8r','hg18','hg18r')])
    gene_identifier = models.CharField(max_length=50, blank=False)
    
    class Meta: db_table = 'genome_reference"."gene_identifier'

class GeneDetail(models.Model):
    '''
    Gene details, keyed to unique genes.
    '''
    gene_identifier     = models.ForeignKey(GeneIdentifier)
    unigene_identifier  = models.CharField(max_length=255, blank=True)
    ensembl_identifier  = models.CharField(max_length=255, blank=True)
    gene_name           = models.CharField(max_length=255, blank=True)
    gene_alias          = models.CharField(max_length=255, blank=True)
    gene_description    = models.CharField(max_length=255, blank=True)
    
    class Meta: db_table = 'genome_reference"."gene_detail'
 
#######################################################
# Transcription Start Sites
#######################################################
class GenomeTSSFactory(object):
    '''
    Given a genome type, return the desired GenomeTSS model.
    '''
    def get_genome_tss(self, genome=''):
        return globals()[genome + 'TSS']
    
class GenomeTSS(models.Model):
    '''
    Mappings of transcription start sites.
    '''
    gene_identifier     = models.ForeignKey(GeneIdentifier)
    chromosome          = models.CharField(max_length=20)
    start               = models.IntegerField(max_length=12)
    end                 = models.IntegerField(max_length=12)
    direction           = models.IntegerField(max_length=1, help_text='0 for forward, 1 for backwards')
    
    class Meta:
        abstract = True
        
class mm9TSS(GenomeTSS):
    ''' Mus musculus, RefSeq 2007. '''
    class Meta: db_table = 'genome_reference"."mm9_tss'
    
class mm8TSS(GenomeTSS):
    ''' Mus musculus, RefSeq 2006. '''
    class Meta: db_table = 'genome_reference"."mm8_tss'

class mm8rTSS(GenomeTSS):
    ''' Mus musculus, RefSeq 2007, masked. '''
    class Meta: db_table = 'genome_reference"."mm8r_tss'
    
class hg18TSS(GenomeTSS):
    ''' Human, RefSeq 2006. '''
    class Meta: db_table = 'genome_reference"."hg18_tss'

class hg18rTSS(GenomeTSS):
    ''' Mus musculus, RefSeq 2006, masked. '''
    class Meta: db_table = 'genome_reference"."hg18r_tss'
    
