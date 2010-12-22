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
from glasslab.utils.database import execute_query,\
    execute_query_without_transaction
import os
from random import randint
from django.db.models.aggregates import Count, Max, Sum

MAX_GAP = 200 # Max gap between transcripts from the same run
MAX_STITCHING_GAP = 10 # Max gap between transcripts being stitched together
MIN_SCORE = 1.4 # Delete transcripts with scores below this threshold.

def multiprocess_all_chromosomes(func, cls, *args):
    ''' 
    Convenience method for splitting up queries based on glass tag id.
    '''
    processes = current_settings.ALLOWED_PROCESSES
    p = Pool(processes)
        
    if not current_settings.CHR_LISTS:
        connection.close()
        try:
            all_chr = Chromosome.objects.values('id').annotate(row_count=Count(cls.__name__.lower())
                                        ).order_by('-row_count').filter(row_count__gt=0)
            all_chr = [chr['id'] for chr in all_chr]
            if not all_chr: raise Exception
        except Exception:
            # cls in question does not have explicit relation to chromosomes; get all
            all_chr = Chromosome.objects.order_by('?').values_list('id', flat=True)
        total_count = len(all_chr)
        # Chromosomes are sorted by count descending, so we want to interleave them
        # in order to create even-ish groups.
        current_settings.CHR_LISTS = [[all_chr[x] for x in xrange(i,total_count,processes)] 
                                                    for i in xrange(0,processes)]
  
    for chr_list in current_settings.CHR_LISTS:
        p.apply_async(func, args=[cls, chr_list,] + list(args))
    p.close()
    p.join()
    
def wrap_add_transcripts_from_groseq(cls, chr_list, *args): wrap_errors(cls._add_transcripts_from_groseq, chr_list, *args)

def wrap_stitch_together_transcripts(cls, chr_list): wrap_errors(cls._stitch_together_transcripts, chr_list)
def wrap_set_scores(cls, chr_list): wrap_errors(cls._set_scores, chr_list)
def wrap_associate_nucleotides(cls, chr_list): wrap_errors(cls._associate_nucleotides, chr_list)
def wrap_force_vacuum(cls, chr_list): wrap_errors(cls._force_vacuum, chr_list)
def wrap_toggle_autovacuum(cls, chr_list, *args): wrap_errors(cls._toggle_autovacuum, chr_list, *args)

class TranscriptBase(models.Model):
    '''
    Unique transcribed regions in the genome, as determined via GRO-Seq.
    '''   
    # Use JS for browser link to auto-include in Django Admin form 
    ucsc_session_url = 'http%3A%2F%2Fbiowhat.ucsd.edu%2Fkallison%2Fucsc%2Fsessions%2F'
    ucsc_browser_link = '''<a href="#" onclick="window.open('http://genome.ucsc.edu/cgi-bin/hgTracks?'''\
                        + '''hgS_doLoadUrl=submit&amp;hgS_loadUrlName=%s' ''' % ucsc_session_url\
                        + ''' + django.jQuery('form')[0].id.replace('_form','').replace('filtered','') + '_' '''\
                        + ''' + (django.jQuery('#id_strand').val()=='0' && 'sense' || 'antisense') + '_strands.txt&db='''\
                        + current_settings.REFERENCE_GENOME + '''&amp;position=' + '''\
                        + ''' django.jQuery('#id_chromosome').attr('title') '''\
                        + ''' + '%3A+' + django.jQuery('#id_transcription_start').val() '''\
                        + ''' + '-' + django.jQuery('#id_transcription_end').val(),'Glass Atlas UCSC View ' + '''\
                        + str(randint(100,99999)) + '''); return false;"'''\
                        + ''' >View in UCSC Browser</a> '''
                        
    chromosome              = models.ForeignKey(Chromosome, help_text=ucsc_browser_link)
    strand                  = models.IntegerField(max_length=1, help_text='0 for +, 1 for -')
    transcription_start     = models.IntegerField(max_length=12)
    transcription_end       = models.IntegerField(max_length=12)
    
    start_end               = CubeField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL cube type.')
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return '%s %d: %s: %d-%d' % (self.__class__.__name__, self.id,
                                  self.chromosome.name.strip(), 
                                  self.transcription_start, 
                                  self.transcription_end)
    
    @classmethod 
    def add_from_tags(cls,  tag_table):
        connection.close()
        sequencing_run = SequencingRun.objects.get(source_table=tag_table)
        if sequencing_run.type.strip() == 'Gro-Seq':
            cls.add_transcripts_from_groseq(tag_table, sequencing_run)
        elif sequencing_run.type.strip() == 'RNA-Seq':
            cls.add_transcribed_rna_from_rnaseq(tag_table, sequencing_run)
            
    ################################################
    # Maintenance
    ################################################
    @classmethod
    def force_vacuum(cls):
        '''
        VACUUM ANALYZE all tables.
        '''
        print 'Vacuum analyzing all tables.'
        for model in (cls, GlassTranscriptSource,
                      GlassTranscriptNucleotides, GlassTranscriptSequence,
                      GlassTranscriptNonCoding, GlassTranscriptConserved, GlassTranscriptPatterned):
            execute_query_without_transaction('VACUUM FULL ANALYZE "%s";' % (model._meta.db_table))
        multiprocess_all_chromosomes(wrap_force_vacuum, cls)
    
    @classmethod        
    def _force_vacuum(cls, chr_list):
        for chr_id in chr_list:
            execute_query_without_transaction('VACUUM FULL ANALYZE "%s_%d";' % (
                                                                    GlassTranscript._meta.db_table, 
                                                                    chr_id))

    @classmethod
    def toggle_autovacuum(cls, on=True):
        '''
        Toggle per-table autovacuum enabled state.
        '''
        for model in (cls, GlassTranscriptSource,
                      GlassTranscriptNucleotides, GlassTranscriptSequence,
                      GlassTranscriptNonCoding, GlassTranscriptConserved, GlassTranscriptPatterned):
            execute_query('ALTER TABLE "%s" SET (autovacuum_enabled=%s);' \
                    % (model._meta.db_table, on and 'true' or 'false'))
        multiprocess_all_chromosomes(wrap_toggle_autovacuum, cls, on)
            
    @classmethod        
    def _toggle_autovacuum(cls, chr_list, on):
        for chr_id in chr_list:
            execute_query('ALTER TABLE "%s_%d" SET (autovacuum_enabled=%s);' \
                    % (GlassTranscript._meta.db_table, chr_id, on and 'true' or 'false'))
    
    @classmethod
    def turn_on_autovacuum(cls):
        '''
        Return autovacuum to normal, enabled state once all processing is done.
        '''
        cls.toggle_autovacuum(on=True)
    
    @classmethod
    def turn_off_autovacuum(cls):
        '''
        We want to be able to turn off autovacuuming on a table-by-table basis
        when we are doing large-scale imports of data to prevent the autovacuum
        daemon from spinning up and using up resources before we're ready.
        '''
        cls.toggle_autovacuum(on=False)
        
class GlassTranscript(TranscriptBase):
    spliced                 = models.NullBooleanField(default=None, help_text='Do we have RNA-Seq confirmation?')
    score                   = models.FloatField(null=True, default=None, 
                                    help_text='Total mapped tags x sequencing runs transcribed in / total sequencing runs possible')
    
    class Meta:
        db_table    = 'glass_atlas_%s"."glass_transcript' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        verbose_name= 'Unfiltered Glass transcript'
            
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
                       sequencing_run.source_table.strip(), MAX_GAP)
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
                SELECT glass_atlas_%s.stitch_transcripts_together(%d, %d);
                SELECT glass_atlas_%s.join_subtranscripts(%d);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       chr_id, MAX_STITCHING_GAP,
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
            
class FilteredGlassTranscriptManager(models.Manager):
    def get_query_set(self):
        return super(FilteredGlassTranscriptManager, self).get_query_set().filter(score__gte=MIN_SCORE)
    
class FilteredGlassTranscript(GlassTranscript):
    '''
    Glass Transcripts above a certain score threshhold, filtered for
    easy viewing in the admin.
    '''
    objects = FilteredGlassTranscriptManager()
    class Meta:
        proxy = True
        app_label   = 'Transcription'
        verbose_name= 'Glass transcript'
    
    ################################################
    # Visualization
    ################################################
    @classmethod
    def generate_bed_file(cls, file_path):
        '''
        Generates a BED file (http://genome.ucsc.edu/FAQ/FAQformat.html#format1)
        of all the transcripts and their exons for viewing in the UCSC Genome Browser.
        '''
        from glasslab.glassatlas.datatypes.transcribed_rna import GlassTranscribedRna
        output = 'track name=glass_transcripts description="Glass Atlas Transcripts" useScore=1 itemRgb=On\n'
        max_score = cls.objects.aggregate(max=Max('score'))['max']
        transcripts = cls.objects.order_by('chromosome__id','transcription_start')
        for trans in transcripts:
            # chrom start end name score strand thick_start thick_end colors? exon_count csv_exon_sizes csv_exon_starts
            row = [trans.chromosome.name, str(trans.transcription_start), str(trans.transcription_end), 
                   'Transcript_' + str(trans.id), str((float(trans.score)/max_score)*1000),
                   trans.strand and '-' or '+', str(trans.transcription_start), str(trans.transcription_end), 
                   trans.strand and '0,255,0' or '0,255,255']
            
            # Add in exons
            # Note: 1 bp start and end exons added because UCSC checks that start and end of 
            # whole transcript match the start and end of the first and last blocks, respectively
            exons = GlassTranscribedRna.objects.filter(glass_transcript=trans
                                    ).annotate(tags=Sum('glasstranscribedrnasource__tag_count')
                                    ).filter(tags__gt=1).order_by('transcription_start')
            row += [str(exons.count() + 2),
                    ','.join(['1'] +
                             [str(min(trans.transcription_end - ex.transcription_start,
                                ex.transcription_end - ex.transcription_start)) for ex in exons] + ['1']),
                    ','.join(['0'] +
                             [str(max(0, ex.transcription_start - trans.transcription_start)) for ex in exons] 
                                + [str(trans.transcription_end - trans.transcription_start - 1)]),
                    ]
        
            output += '\t'.join(row) + '\n'
        
        f = open(file_path, 'w')
        f.write(output)
        f.close()
        
            
          
class GlassTranscriptNucleotides(models.Model):
    glass_transcript  = models.ForeignKey(GlassTranscript)
    sequence          = models.TextField()
    
    class Meta:
        db_table    = 'glass_atlas_%s"."glass_transcript_nucleotides' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        verbose_name = 'Glass transcript nucleotide sequence'
        
    def __unicode__(self):
        return 'GlassTranscriptNucleotides for transcript %d' % (self.glass_transcript.id)
       

class TranscriptSourceBase(models.Model):
    sequencing_run          = models.ForeignKey(SequencingRun)
    tag_count               = models.IntegerField(max_length=12)
    gaps                    = models.IntegerField(max_length=12)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return '%s: %d tags from %s' % (self.__class__.__name__,
                                          self.tag_count,
                                          self.sequencing_run.source_table.strip())
        
class GlassTranscriptSource(TranscriptSourceBase):
    glass_transcript        = models.ForeignKey(GlassTranscript)
    
    class Meta:
        db_table    = 'glass_atlas_%s"."glass_transcript_source' % current_settings.TRANSCRIPT_GENOME
        app_label   = 'Transcription'
        
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
    