'''
Created on Sep 24, 2010

@author: karmel
'''
from django.db import models
    
#######################################################
# Gene identifiers
#######################################################

class GenomeType(models.Model):
    '''
    Genome types with unique gene records.
    '''
    genome_type = models.CharField(max_length=20)
    
    class Meta: db_table = 'genome_reference"."genome_type'

class Genome(models.Model):
    '''
    Genomes for which we store data.
    '''
    genome_type = models.ForeignKey(GenomeType)
    genome      = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    
    class Meta: db_table = 'genome_reference"."genome'
    
class SequenceIdentifier(models.Model):
    '''
    Gene and sequence (i.e., noncoding RNA) identifiers from RefSeq, unique per genome.
    '''
    genome_type         = models.ForeignKey(GenomeType)
    sequence_identifier = models.CharField(max_length=50, blank=False)
    
    class Meta: db_table = 'genome_reference"."sequence_identifier'
    
    @classmethod
    def get_with_fallback(cls, *args, **kwargs):
        ''' 
        Try to get sequence id directly first; if that fails, check aliases.
        
        Requires that sequence_identifier be passed in.
        '''
        try: return cls.objects.get(*args,**kwargs)
        except cls.DoesNotExist:
            kwargs['alias'] = kwargs.get('sequence_identifier')
            del kwargs['sequence_identifier']
            return SequenceAlias.objects.get(*args, **kwargs).sequence_identifier

class SequenceAlias(models.Model):
    '''
    Unique identifiers for sequence fragments, keyed to single parent sequence identifier.
    If self is same as parent, keyed to self.
    '''
    genome_type         = models.ForeignKey(GenomeType)
    alias               = models.CharField(max_length=50, blank=False)
    sequence_identifier = models.ForeignKey(SequenceIdentifier, help_text='Main identifier.')
    
    class Meta: db_table = 'genome_reference"."sequence_alias'

class GeneDetail(models.Model):
    '''
    Gene details, keyed to unique sequences.
    '''
    sequence_identifier = models.ForeignKey(SequenceIdentifier)
    unigene_identifier  = models.CharField(max_length=255, blank=True)
    ensembl_identifier  = models.CharField(max_length=255, blank=True)
    gene_name           = models.CharField(max_length=255, blank=True)
    gene_alias          = models.CharField(max_length=255, blank=True)
    gene_description    = models.CharField(max_length=255, blank=True)
    refseq_gene_id      = models.IntegerField(max_length=12, blank=True)
    
    class Meta: db_table = 'genome_reference"."gene_detail'
 
#######################################################
# Chromosome location details 
#######################################################
class TranscriptionStartSite(models.Model):
    '''
    Mappings of transcription start sites.
    '''
    genome              = models.ForeignKey(Genome)
    sequence_identifier = models.ForeignKey(SequenceIdentifier)
    chromosome          = models.CharField(max_length=20)
    start               = models.IntegerField(max_length=12)
    end                 = models.IntegerField(max_length=12)
    direction           = models.IntegerField(max_length=1, help_text='0 for forward, 1 for backwards')
    
    class Meta: db_table = 'genome_reference"."transcription_start_site'

class ChromosomeLocationAnnotation(models.Model):
    '''
    Mappings of locations to introns, exons, etc.
    
    Abstract model; there are a sufficient number of rows that it is useful
    to separate these by genome.
    '''
    chromosome      = models.CharField(max_length=20)
    start           = models.IntegerField(max_length=12)
    end             = models.IntegerField(max_length=12)
    direction       = models.IntegerField(max_length=1, help_text='0 for forward, 1 for backwards')
    type            = models.CharField(max_length=20, choices=[((x,x) for x in ('Intron','Exon','CpG Island',
                                                                                'Intergenic','Promoter',
                                                                                "3' UTR", "5' UTR"))])
    description     = models.CharField(max_length=255, blank=True)
    
    class Meta: abstract = True

class ChromosomeLocationAnnotationMm8(ChromosomeLocationAnnotation):
    class Meta: db_table = 'genome_reference"."chromosome_location_annotation_mm8'
class ChromosomeLocationAnnotationMm8r(ChromosomeLocationAnnotation):
    class Meta: db_table = 'genome_reference"."chromosome_location_annotation_mm8r'
class ChromosomeLocationAnnotationMm9(ChromosomeLocationAnnotation):
    class Meta: db_table = 'genome_reference"."chromosome_location_annotation_mm9'
class ChromosomeLocationAnnotationHg18(ChromosomeLocationAnnotation):
    class Meta: db_table = 'genome_reference"."chromosome_location_annotation_hg18'
class ChromosomeLocationAnnotationHg18r(ChromosomeLocationAnnotation):
    class Meta: db_table = 'genome_reference"."chromosome_location_annotation_hg18r'

class ChromosomeLocationAnnotationFactory(object):
    '''
    Factory for getting appropriate model by genome.
    '''
    @classmethod
    def get_model(cls, genome):
        return globals()['ChromosomeLocationAnnotation%s' % genome.capitalize()]
    