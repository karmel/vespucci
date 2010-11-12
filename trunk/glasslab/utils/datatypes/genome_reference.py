'''
Created on Sep 24, 2010

@author: karmel

.. attention::
    
    All sequence indices assume a start position of 0, as per the UCSC Genome Browser standard.

'''
from django.db import models
from glasslab.config import current_settings
from glasslab.utils.datatypes.basic_model import CubeField
    
#######################################################
# Genome identifiers
#######################################################

class GenomeType(models.Model):
    '''
    Genome types with unique gene records.
    '''
    genome_type = models.CharField(max_length=20)
    
    class Meta: 
        db_table    = 'genome_reference"."genome_type'
        app_label   = 'Genome_Reference'

class Genome(models.Model):
    '''
    Genomes for which we store data.
    '''
    genome_type = models.ForeignKey(GenomeType)
    genome      = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    
    class Meta: 
        db_table    = 'genome_reference"."genome'
        app_label   = 'Genome_Reference'

class KeggPathway(models.Model):
    '''
    Kegg Pathway descriptions
    '''
    pathway_key = models.CharField(max_length=10, help_text='Identifier string for the pathway (i.e., "mmu00051"')
    description = models.CharField(max_length=255)
    
    class Meta: 
        db_table    = 'genome_reference"."kegg_pathway'
        app_label   = 'Genome_Reference'
    
    def __unicode__(self): return self.description
    
#######################################################
# Per-genome Gene identifiers
#######################################################
class Chromosome(models.Model):
    '''
    Unique record of chromosome, i.e. 'chr1', 'chrUn_random', etc
    '''
    name = models.CharField(max_length=25, blank=False)
    
    class Meta: 
        db_table    = 'genome_reference_%s"."chromosome' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'
    
    def __unicode__(self): return self.name

class SequenceIdentifier(models.Model):
    '''
    Gene and sequence (i.e., noncoding RNA) identifiers from RefSeq, unique per genome.
    '''
    sequence_identifier = models.CharField(max_length=50, blank=False)
    
    class Meta: 
        db_table    = 'genome_reference_%s"."sequence_identifier' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'
    
    def __unicode__(self): return self.sequence_identifier
    
    _sequence_detail = None
    @property 
    def sequence_detail(self):
        if not self._sequence_detail:
            detail = SequenceDetail.objects.filter(sequence_identifier=self).order_by('-gene_name')[:1]
            if detail: self._sequence_detail =  detail[0]
        return self._sequence_detail
    
    _sequence_transcription_region = None
    @property 
    def sequence_transcription_region(self):
        if not self._sequence_transcription_region:
            reg = SequenceTranscriptionRegion.objects.filter(sequence_identifier=self).order_by('transcription_start')[:1]
            if reg: self._sequence_transcription_region =  reg[0]
        return self._sequence_transcription_region

class SequenceDetail(models.Model):
    '''
    Gene details, keyed to unique sequences.
    '''
    sequence_identifier = models.ForeignKey(SequenceIdentifier)
    gene_name           = models.CharField(max_length=100, blank=True)
    description         = models.CharField(max_length=255, blank=True)
    ensembl_id          = models.CharField(max_length=100, blank=True)
    pfam_id             = models.CharField(max_length=100, blank=True)
    
    class Meta: 
        db_table    = 'genome_reference_%s"."sequence_detail' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'
    
    def __unicode__(self): 
        return '%s (%s)' % (self.gene_name, self.sequence_identifier.sequence_identifier)
 
#######################################################
# Chromosome region details 
#######################################################
class SequenceTranscriptionRegion(models.Model):
    '''
    Mappings of transcription regions and coding sites.
    '''
    sequence_identifier = models.ForeignKey(SequenceIdentifier)
    chromosome          = models.ForeignKey(Chromosome)
    bin                 = models.IntegerField(max_length=5, help_text='Base-2 determined bin.')
    strand              = models.IntegerField(max_length=1, help_text='0 for +, 1 for -')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end   = models.IntegerField(max_length=12)    
    coding_start        = models.IntegerField(max_length=12)
    coding_end          = models.IntegerField(max_length=12)
    
    start_end           = CubeField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL cube type.')
    
    class Meta: 
        db_table    = 'genome_reference_%s"."sequence_transcription_region' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'

    def __unicode__(self):
        return 'Sequence Transcription Region for %s' % self.sequence_identifier.sequence_identifier.strip()
    
class SequenceExon(models.Model):
    '''
    Mappings of transcription regions and coding sites.
    '''
    sequence_transcription_region = models.ForeignKey(SequenceTranscriptionRegion)
    exon_start = models.IntegerField(max_length=12)
    exon_end   = models.IntegerField(max_length=12)    
    frame      = models.IntegerField(max_length=5, help_text='Number o nucleotides needed from prior exon to make a complete amino acid at the start of this exon.')
    
    class Meta: 
        db_table    = 'genome_reference_%s"."sequence_exon' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'
    
class SequenceKeggPathway(models.Model):
    '''
    Mappings of transcription regions and coding sites.
    '''
    sequence_identifier = models.ForeignKey(SequenceIdentifier)
    kegg_pathway        = models.ForeignKey(KeggPathway)
    map_location        = models.CharField(max_length=50, help_text='Mappable identifier for this sequence and pathway; can be used in Kegg URLs.')
    
    class Meta: 
        db_table    = 'genome_reference_%s"."sequence_kegg_pathway' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'

class NonCodingRna(models.Model):
    '''
    Unique name and type for ncRNA
    
    '''
    type                = models.CharField(max_length=20)
    name                = models.CharField(max_length=100)
    
    class Meta: 
        db_table    = 'genome_reference_%s"."non_coding_rna' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'
    
    def __unicode__(self):
        return '%s %s' % (self.type, self.name.strip())
    
    _non_coding_transcription_region = None
    @property 
    def non_coding_transcription_region(self):
        if not self._non_coding_transcription_region:
            reg = NonCodingTranscriptionRegion.objects.filter(non_coding_rna=self).order_by('transcription_start')[:1]
            if reg: self._non_coding_transcription_region =  reg[0]
        return self._non_coding_transcription_region
    
class NonCodingTranscriptionRegion(models.Model):
    '''
    Mappings of transcription regions that are not tied to RefSeq genes.
    
    Scores are 0 - 1000, higher indicating that the sequence is more likely to be true ncRNA.
    
    '''
    non_coding_rna      = models.ForeignKey(NonCodingRna)
    chromosome          = models.ForeignKey(Chromosome)
    bin                 = models.IntegerField(max_length=5, help_text='Base-2 determined bin.')
    strand              = models.IntegerField(max_length=1, help_text='0 for +, 1 for -')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end   = models.IntegerField(max_length=12)    
    score               = models.IntegerField(max_length=5)
    
    start_end           = CubeField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL cube type.')
    
    class Meta: 
        db_table    = 'genome_reference_%s"."non_coding_transcription_region' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'

    def __unicode__(self):
        return '%s Transcription Region for %s' % (self.non_coding_rna.type, self.non_coding_rna.name.strip())
    
class PatternedTranscriptionRegion(models.Model):
    '''
    Mappings of patterns-- i.e., repeats-- onto transcription regions.
    '''
    type                = models.CharField(max_length=20)
    name                = models.CharField(max_length=100)
    chromosome          = models.ForeignKey(Chromosome)
    bin                 = models.IntegerField(max_length=5, help_text='Base-2 determined bin.')
    strand              = models.IntegerField(max_length=1, help_text='0 for +, 1 for -. Default NULL')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end   = models.IntegerField(max_length=12)
    
    start_end           = CubeField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL cube type.')
    
    class Meta: 
        db_table    = 'genome_reference_%s"."patterned_transcription_region' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'

    def __unicode__(self):
        return 'Patterned Transcription Region for %s %s' % (self.type, self.name.strip())
    
class ConservedTranscriptionRegion(models.Model):
    '''
    Coservation records for transcription regions determined by the phastCons HMM algorithm.
    
    Scores are 0 - 1000, higher indicating more likely to be a conserved region.
    
    More on the scores: http://genome.ucsc.edu/goldenPath/help/phastCons.html
    
    Siepel A and Haussler D (2005). Phylogenetic hidden Markov models. In R. Nielsen, ed., 
    Statistical Methods in Molecular Evolution, pp. 325-351, Springer, New York.
    
    '''
    chromosome          = models.ForeignKey(Chromosome)
    bin                 = models.IntegerField(max_length=5, help_text='Base-2 determined bin.')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end   = models.IntegerField(max_length=12)
    score               = models.IntegerField(max_length=5)
    
    start_end           = CubeField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL cube type.')
    
    class Meta: 
        db_table    = 'genome_reference_%s"."conserved_transcription_region' % current_settings.REFERENCE_GENOME
        app_label   = 'Genome_Reference'

    def __unicode__(self):
        return 'Conserved Transcription Region with score %d' % self.score