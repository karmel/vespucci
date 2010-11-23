'''
Created on Nov 8, 2010

@author: karmel
'''
from __future__ import division
from glasslab.config import current_settings
from django.db import models, connection
from glasslab.utils.datatypes.genome_reference import Chromosome,\
    SequenceTranscriptionRegion, PatternedTranscriptionRegion,\
    ConservedTranscriptionRegion, NonCodingTranscriptionRegion
from glasslab.glassatlas.datatypes.metadata import SequencingRun
from glasslab.sequencing.datatypes.tag import multiprocess_glass_tags,\
    wrap_errors
from glasslab.utils.datatypes.basic_model import CubeField
from multiprocessing import Pool
from glasslab.utils.database import execute_query
import os

MAX_SEQUENCE_GAP = 2000 # Max gap between transcripts that share sequence associations
MAX_OTHER_GAP = 200 # Max gap between transcripts that share no sequence associations
MIN_SCORE = 1 # Delete transcripts with scores below this threshold.

def multiprocess_all_chromosomes(func, cls, *args):
    ''' 
    Convenience method for splitting up queries based on glass tag id.
    '''
    connection.close()
    all_chr = Chromosome.objects.order_by('?').values_list('id', flat=True)
    total_count = len(all_chr)
    processes = 6
    p = Pool(processes)
    # Chromosomes are sorted by count descending, so we want to interleave them
    # in order to create even-ish groups.
    chr_lists = [[all_chr[x] for x in xrange(i,total_count,processes)] 
                                for i in xrange(0,processes)]
    
    for chr_list in chr_lists:
        p.apply_async(func, args=[cls, chr_list,] + list(args))
    p.close()
    p.join()
    
def wrap_add_transcripts_from_groseq(cls, chr_list, *args): wrap_errors(cls._add_transcripts_from_groseq, chr_list, *args)
def wrap_add_transcripts_from_rnaseq(cls, chr_list, *args): wrap_errors(cls._add_transcripts_from_rnaseq, chr_list, *args)

def wrap_stitch_together_transcripts(cls, chr_list): wrap_errors(cls._stitch_together_transcripts, chr_list)
def wrap_set_scores(cls, chr_list): wrap_errors(cls._set_scores, chr_list)
def wrap_associate_nucleotides(cls, chr_list): wrap_errors(cls._associate_nucleotides, chr_list)

class GlassTranscript(models.Model):
    '''
    Unique transcribed regions in the genome.
    '''   
    # Use JS for browser link to auto-include in Django Admin form 
    ucsc_browser_link = '''<a href="#" onclick="window.open('http://genome.ucsc.edu/cgi-bin/hgTracks?'''\
                        + '''hgS_doLoadUrl=submit&amp;hgS_loadUrlName=http%3A%2F%2Fbiowhat.ucsd.edu%2Fkallison%2Fucsc%2Fsessions%2Fgro_seq.txt&db='''\
                        + current_settings.REFERENCE_GENOME + '''&amp;position=' + '''\
                        + ''' document.getElementById('id_chromosome').title '''\
                        + ''' + '%3A+' + document.getElementById('id_transcription_start').value '''\
                        + ''' + '-' + document.getElementById('id_transcription_end').value,'GlassTranscript' + '''\
                        + ''' document.getElementById('id_glasstranscriptsource_set-0-id').value); return false;"'''\
                        + ''' >View in UCSC Browser</a> '''
                        
    chromosome              = models.ForeignKey(Chromosome, help_text=ucsc_browser_link)
    strand_0                = models.BooleanField(default=False, help_text='Do we see tags on the + strand?')
    strand_1                = models.BooleanField(default=False, help_text='Do we see tags on the - strand?')
    transcription_start     = models.IntegerField(max_length=12)
    transcription_end       = models.IntegerField(max_length=12)
    
    spliced                 = models.NullBooleanField(default=None, help_text='Do we have RNA-Seq confirmation?')
    score                   = models.FloatField(null=True, default=None, 
                                    help_text='Total mapped tags x sequencing runs transcribed in / total sequencing runs possible')
    
    start_end               = CubeField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL cube type.')
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table    = 'glass_atlas_%s"."glass_transcript' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        
    def __unicode__(self):
        return 'GlassTranscript: %s: %d-%d' % (self.chromosome.name.strip(), 
                                               self.transcription_start, 
                                               self.transcription_end)
    
    @classmethod 
    def add_transcripts_from_tags(cls,  tag_table):
        sequencing_run = SequencingRun.objects.get(source_table=tag_table)
        if sequencing_run.type.strip() == 'Gro-Seq':
            cls.add_transcripts_from_groseq(tag_table, sequencing_run)
        elif sequencing_run.type.strip() == 'RNA-Seq':
            cls.add_transcripts_from_rnaseq(tag_table, sequencing_run)
            
    ################################################
    # GRO-Seq to transcripts
    ################################################
    @classmethod 
    def add_transcripts_from_groseq(cls,  tag_table, sequencing_run):
        multiprocess_glass_tags(wrap_add_transcripts_from_groseq, cls, sequencing_run)
        #wrap_add_transcripts_from_tags(cls,[21, 22],sequencing_run)
        
    @classmethod
    def _add_transcripts_from_groseq(cls, chr_list, sequencing_run):
        for chr_id in chr_list:
            print 'Adding transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s.save_transcripts_from_sequencing_run(%d, %d,'%s', %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       sequencing_run.id, chr_id, 
                       sequencing_run.source_table.strip(), MAX_OTHER_GAP)
            execute_query(query)
    
    ################################################
    # RNA-Seq to transcripts
    ################################################            
    @classmethod 
    def add_tags_from_rnaseq(cls,  tag_table, sequencing_run):
        multiprocess_glass_tags(wrap_add_transcripts_from_rnaseq, cls, sequencing_run)
        
    @classmethod
    def _add_transcripts_from_rnaseq(cls, chr_list, sequencing_run):
        for chr_id in chr_list:
            print 'Adding transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s.save_transcripts_from_sequencing_run(%d, %d,'%s', %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       sequencing_run.id, chr_id, 
                       sequencing_run.source_table.strip(), MAX_OTHER_GAP)
            execute_query(query)
            
    ################################################
    # Transcript cleanup and refinement
    ################################################
    @classmethod
    def stitch_together_transcripts(cls):
        multiprocess_all_chromosomes(wrap_stitch_together_transcripts, cls)
        #wrap_stitch_together_transcripts(cls,[21, 22])
    
    @classmethod
    def _stitch_together_transcripts(cls, chr_list):
        for chr_id in chr_list:
            print 'Stitching together transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s.stitch_transcripts_together(%d, %d, %d);
                SELECT glass_atlas_%s.join_subtranscripts(%d);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       chr_id, MAX_SEQUENCE_GAP, MAX_OTHER_GAP,
                       current_settings.TRANSCRIPT_GENOME, 
                       chr_id)
            execute_query(query)
            
    @classmethod
    def set_scores(cls):
        multiprocess_all_chromosomes(wrap_set_scores, cls)
        #wrap_set_scores(cls,[21, 22])
    
    @classmethod
    def _set_scores(cls, chr_list):
        for chr_id in chr_list:
            print 'Scoring transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s.calculate_scores(%d);
                """ % (current_settings.TRANSCRIPT_GENOME, chr_id)
            execute_query(query)
            
    @classmethod
    def delete_invalid_transcripts(cls):
        '''
        Delete transcripts falling below a certain score threshold.
        '''
        query = """
            DELETE FROM  "%s" WHERE score IS NOT NULL AND score < %d;
            """ % (GlassTranscript._meta.db_table, MIN_SCORE)
        execute_query(query)
        print 'Deleted transcripts below score threshold of %d' % MIN_SCORE    
    
    @classmethod
    def associate_nucleotides(cls):
        multiprocess_all_chromosomes(wrap_associate_nucleotides, cls)
        #wrap_associate_nucleotides(cls,[1])
        
    @classmethod
    def _associate_nucleotides(cls, chr_list):
        '''
        Pull and store sequence strings for transcripts for only those transcripts
        that have been updated (score is null).
        
        Sequences information is stored in the local filesystem.
        '''
        for chr_id in chr_list:
            connection.close()
            
            print 'Obtaining coding sequence for transcripts in chromosome %d' % chr_id
            path = current_settings.GENOME_ASSEMBLY_PATHS[current_settings.REFERENCE_GENOME]
            path = os.path.join(path, '%s.fa' % Chromosome.objects.get(id=chr_id).name.strip())
            
            fasta = map(lambda x: x[:-1], file(path).readlines()) # Read file and ditch '\n'
            fasta = fasta[1:] # Ditch the first line, which is the chromosome identifier
            length = len(fasta[0])
            
            for transcript in cls.objects.filter(chromosome__id=chr_id, score__isnull=True):
                start = transcript.transcription_start
                stop = transcript.transcription_end
                beginning = fasta[start//length][start % length - 1:]
                end = fasta[stop//length][:stop % length]
                middle = fasta[(start//length + 1):(stop//length)]
                seq = (beginning + ''.join(middle) + end).upper()
                try: sequence = GlassTranscriptNucleotides.objects.get(glass_transcript=transcript)
                except GlassTranscriptNucleotides.DoesNotExist:
                    sequence = GlassTranscriptNucleotides(glass_transcript=transcript)
                sequence.sequence = seq
                sequence.save()
            connection.close()
            
class GlassTranscriptNucleotides(models.Model):
    glass_transcript  = models.ForeignKey(GlassTranscript)
    sequence          = models.TextField()
    
    class Meta:
        db_table    = 'glass_atlas_%s"."glass_transcript_nucleotides' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        verbose_name = 'Glass transcript nucleotide sequence'
        
    def __unicode__(self):
        return 'GlassTranscriptNucleotides for transcript %d' % (self.glass_transcript.id)
       
class GlassTranscriptSource(models.Model):
    glass_transcript        = models.ForeignKey(GlassTranscript)
    sequencing_run          = models.ForeignKey(SequencingRun)
    tag_count               = models.IntegerField(max_length=12)
    gaps                    = models.IntegerField(max_length=12)
    
    class Meta:
        db_table    = 'glass_atlas_%s"."glass_transcript_source' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        
    def __unicode__(self):
        return 'GlassTranscriptSource: %d tags for transcript %d from %s' % (self.tag_count,
                                                                             self.glass_transcript.id,
                                                                             self.sequencing_run.source_table.strip())
        
class GlassTranscriptTranscriptionRegionTable(models.Model):
    glass_transcript= models.ForeignKey(GlassTranscript)
    relationship    = models.CharField(max_length=100, choices=[(x,x) 
                                                    for x in ('contains','is contained by','overlaps with','is equal to')])
    
    table_type      = None
    related_class   = None    
    
    class Meta: 
        abstract = True        
    
    def __unicode__(self):
        return 'GlassTranscript %d %s %s' % (self.glass_transcript.id, 
                                             self.relationship.strip(), 
                                             str(self.foreign_key_field()))    
    
    def foreign_key_field(self): 
        return getattr(self, '%s_transcription_region' % self.table_type)
    
    @classmethod
    def get_children(cls):
        return (GlassTranscriptSequence, GlassTranscriptNonCoding,
                GlassTranscriptConserved, GlassTranscriptPatterned)
        
class GlassTranscriptSequence(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the sequence record it maps to.
    '''
    sequence_transcription_region   = models.ForeignKey(SequenceTranscriptionRegion)
    
    table_type = 'sequence'
    related_class = SequenceTranscriptionRegion
    
    class Meta: 
        db_table    = 'glass_atlas_%s"."glass_transcript_sequence' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        verbose_name = 'Glass transcript sequence region'
           
class GlassTranscriptNonCoding(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the non coding region it maps to.
    '''
    non_coding_transcription_region = models.ForeignKey(NonCodingTranscriptionRegion)
    
    table_type = 'non_coding'
    related_class = NonCodingTranscriptionRegion

    class Meta: 
        db_table    = 'glass_atlas_%s"."glass_transcript_non_coding' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        verbose_name = 'Glass transcript non-coding region'
        
class GlassTranscriptPatterned(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the patterned region it maps to.
    '''
    patterned_transcription_region  = models.ForeignKey(PatternedTranscriptionRegion)
    
    table_type      = 'patterned'
    related_class   = PatternedTranscriptionRegion
    
    class Meta: 
        db_table    = 'glass_atlas_%s"."glass_transcript_patterned' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        verbose_name = 'Glass transcript patterned region'
        
class GlassTranscriptConserved(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the conservation region it maps to.
    '''
    conserved_transcription_region  = models.ForeignKey(ConservedTranscriptionRegion)
    
    table_type      = 'conserved'
    related_class   = ConservedTranscriptionRegion

    class Meta: 
        db_table    = 'glass_atlas_%s"."glass_transcript_conserved' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        verbose_name = 'Glass transcript conserved region'
    