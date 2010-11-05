'''
Created on Sep 24, 2010

@author: karmel

.. attention::
    
    All sequence indices assume a start position of 0, as per the UCSC Genome Browser standard.

'''
from django.db import models
from glasslab.config import current_settings
    
#######################################################
# Genome identifiers
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

class KeggPathway(models.Model):
    '''
    Kegg Pathway descriptions
    '''
    pathway_key = models.CharField(max_length=10, help_text='Identifier string for the pathway (i.e., "mmu00051"')
    description = models.CharField(max_length=255)
    
    class Meta: db_table = 'genome_reference"."kegg_pathway'
    
#######################################################
# Per-genome Gene identifiers
#######################################################
class Chromosome(models.Model):
    '''
    Unique record of chromosome, i.e. 'chr1', 'chrUn_random', etc
    '''
    name = models.CharField(max_length=25, blank=False)
    
    class Meta: db_table = 'genome_reference_%s"."chromosome' % current_settings.GENOME

class SequenceIdentifier(models.Model):
    '''
    Gene and sequence (i.e., noncoding RNA) identifiers from RefSeq, unique per genome.
    '''
    sequence_identifier = models.CharField(max_length=50, blank=False)
    
    class Meta: db_table = 'genome_reference_%s"."sequence_identifier' % current_settings.GENOME
    
    _sequence_detail = None
    @property 
    def sequence_detail(self):
        if not self._sequence_detail:
            self._sequence_detail = SequenceDetail.objects.get(sequence_identifier=self)
        return self._sequence_detail

class SequenceDetail(models.Model):
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
    
    class Meta: db_table = 'genome_reference_%s"."sequence_detail' % current_settings.GENOME
 
#######################################################
# Chromosome region details 
#######################################################
class SequenceTranscriptionRegion(models.Model):
    '''
    Mappings of transcription regions and coding sites.
    '''
    sequence_identifier = models.ForeignKey(SequenceIdentifier)
    full_bin            = models.IntegerField(max_length=7, help_text='5 digit, left-padded, bin, plus id of chromosome.')
    chromosome          = models.ForeignKey(Chromosome)
    bin                 = models.IntegerField(max_length=5, help_text='Base-2 determined bin.')
    strand              = models.IntegerField(max_length=1, help_text='0 for +, 1 for -')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end   = models.IntegerField(max_length=12)    
    coding_start        = models.IntegerField(max_length=12)
    coding_end          = models.IntegerField(max_length=12)
    
    class Meta: db_table = 'genome_reference_%s"."sequence_transcription_region' % current_settings.GENOME

class SequenceExon(models.Model):
    '''
    Mappings of transcription regions and coding sites.
    '''
    sequence_transcription_region = models.ForeignKey(SequenceTranscriptionRegion)
    exon_start = models.IntegerField(max_length=12)
    exon_end   = models.IntegerField(max_length=12)    
    frame      = models.IntegerField(max_length=5, help_text='Number o nucleotides needed from prior exon to make a complete amino acid at the start of this exon.')
    
    class Meta: db_table = 'genome_reference_%s"."sequence_exon' % current_settings.GENOME
    
class SequenceKeggPathway(models.Model):
    '''
    Mappings of transcription regions and coding sites.
    '''
    sequence_identifier = models.ForeignKey(SequenceIdentifier)
    kegg_pathway        = models.ForeignKey(KeggPathway)
    map_location        = models.CharField(max_length=50, help_text='Mappable identifier for this sequence and pathway; can be used in Kegg URLs.')
    
    class Meta: db_table = 'genome_reference_%s"."sequence_kegg_pathway' % current_settings.GENOME

class NonCodingTranscriptionRegion(models.Model):
    '''
    Mappings of transcription regions that are not tied to RefSeq genes.
    
    Scores are 0 - 1000, higher indicating that the sequence is more likely to be true ncRNA.
    
    '''
    type                = models.CharField(max_length=20)
    name                = models.CharField(max_length=100)
    full_bin            = models.IntegerField(max_length=7, help_text='5 digit, left-padded, bin, plus id of chromosome.')
    chromosome          = models.ForeignKey(Chromosome)
    bin                 = models.IntegerField(max_length=5, help_text='Base-2 determined bin.')
    strand              = models.IntegerField(max_length=1, help_text='0 for +, 1 for -')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end   = models.IntegerField(max_length=12)    
    score               = models.IntegerField(max_length=5)
    
    class Meta: db_table = 'genome_reference_%s"."non_coding_transcription_region' % current_settings.GENOME

class PatternedTranscriptionRegion(models.Model):
    '''
    Mappings of patterns-- i.e., repeats-- onto transcription regions.
    '''
    type                = models.CharField(max_length=20)
    name                = models.CharField(max_length=100)
    full_bin            = models.IntegerField(max_length=7, help_text='5 digit, left-padded, bin, plus id of chromosome.')
    chromosome          = models.ForeignKey(Chromosome)
    bin                 = models.IntegerField(max_length=5, help_text='Base-2 determined bin.')
    strand              = models.IntegerField(max_length=1, help_text='0 for +, 1 for -. Default NULL')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end   = models.IntegerField(max_length=12)
    
    class Meta: db_table = 'genome_reference_%s"."patterned_transcription_region' % current_settings.GENOME

class ConservedTranscriptionRegion(models.Model):
    '''
    Coservation records for transcription regions determined by the phastCons HMM algorithm.
    
    Scores are 0 - 1000, higher indicating more likely to be a conserved region.
    
    More on the scores: http://genome.ucsc.edu/goldenPath/help/phastCons.html
    
    Siepel A and Haussler D (2005). Phylogenetic hidden Markov models. In R. Nielsen, ed., 
    Statistical Methods in Molecular Evolution, pp. 325-351, Springer, New York.
    
    '''
    full_bin            = models.IntegerField(max_length=7, help_text='5 digit, left-padded, bin, plus id of chromosome.')
    chromosome          = models.ForeignKey(Chromosome)
    bin                 = models.IntegerField(max_length=5, help_text='Base-2 determined bin.')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end   = models.IntegerField(max_length=12)
    score               = models.IntegerField(max_length=5)
    
    class Meta: db_table = 'genome_reference_%s"."conserved_transcription_region' % current_settings.GENOME
