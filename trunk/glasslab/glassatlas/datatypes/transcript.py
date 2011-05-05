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
from glasslab.glassatlas.datatypes.metadata import SequencingRun,\
    ExpectedTagCount
from glasslab.sequencing.datatypes.tag import multiprocess_glass_tags,\
    wrap_errors
from glasslab.utils.datatypes.basic_model import BoxField, GlassModel
from multiprocessing import Pool
from glasslab.utils.database import execute_query,\
    execute_query_without_transaction, fetch_rows
import os
from random import randint, sample
from django.db.models.aggregates import Count, Max, Sum
from datetime import datetime

# The tags returned from the sequencing run are shorter than we know them to be biologically
# We can therefore extend the mapped tag region by a set number of bp if an extension is passed in
TAG_EXTENSION = 50

MAX_GAP = 0 # Max gap between transcripts from the same run
MAX_STITCHING_GAP = MAX_GAP # Max gap between transcripts being stitched together
MAX_EDGE = 300 # Max edge length of transcript graph subgraphs to be created
EDGE_SCALING_FACTOR = 20 # Number of transcripts per DENSITY_MULTIPLIER bp required to get full allowed edge length
DENSITY_MULTIPLIER = 1000 # Scaling factor on density-- think of as bps worth of tags to consider
MIN_SCORE = 3 # Hide transcripts with scores below this threshold.

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
            try:
                all_chr = Chromosome.objects.values('id').annotate(
                                row_count=Count(cls.cell_base.glass_transcript_prep.__name__.lower())
                                        ).order_by('-row_count').filter(row_count__gt=0)
                all_chr = [chr['id'] for chr in all_chr]
                if not all_chr: raise Exception
            except Exception:
                # cls in question does not have explicit relation to chromosomes; get all
                all_chr = Chromosome.objects.order_by('?').values_list('id', flat=True)
            
        # Chromosomes are sorted by count descending, so we want to snake them
        # back and forth to create even-ish groups
        chr_sets = [[] for _ in xrange(0, processes)]
        for i,chr in enumerate(all_chr):
            if i and not i % processes: chr_sets.reverse()
            chr_sets[i % processes].append(chr)
             
        current_settings.CHR_LISTS = chr_sets
        
    for chr_list in current_settings.CHR_LISTS:
        p.apply_async(func, args=[cls, chr_list,] + list(args))
    p.close()
    p.join()
    
def wrap_add_transcripts_from_groseq(cls, chr_list, *args): wrap_errors(cls._add_transcripts_from_groseq, chr_list, *args)
def wrap_remove_rogue_run(cls, chr_list): wrap_errors(cls._remove_rogue_run, chr_list)

def wrap_stitch_together_transcripts(cls, chr_list, *args): wrap_errors(cls._stitch_together_transcripts, chr_list, *args)
def wrap_set_density(cls, chr_list, *args): wrap_errors(cls._set_density, chr_list, *args)
def wrap_draw_transcript_edges(cls, chr_list): wrap_errors(cls._draw_transcript_edges, chr_list)
def wrap_set_score_thresholds(cls, chr_list, *args): wrap_errors(cls._set_score_thresholds, chr_list, *args)
def wrap_set_scores(cls, chr_list): wrap_errors(cls._set_scores, chr_list)
def wrap_mark_as_spliced(cls, chr_list): wrap_errors(cls._mark_as_spliced, chr_list)
def wrap_associate_nucleotides(cls, chr_list): wrap_errors(cls._associate_nucleotides, chr_list)
def wrap_force_vacuum(cls, chr_list): wrap_errors(cls._force_vacuum, chr_list)

class CellTypeBase(object):
    cell_type = ''
    
    @classmethod
    def get_correlations(cls):
        from glasslab.glassatlas.datatypes.celltypes.thiomac import ThioMacBase
        return {'thiomac': ThioMacBase,}
          
    @property
    def glass_transcript(self): return GlassTranscript
    @property
    def filtered_glass_transcript(self): return FilteredGlassTranscript
    @property
    def glass_transcript_source(self): return GlassTranscriptSource
    @property
    def glass_transcript_nucleotides(self): return GlassTranscriptNucleotides
    @property
    def glass_transcript_sequence(self): return GlassTranscriptSequence
    @property
    def glass_transcript_non_coding(self): return GlassTranscriptNonCoding
    @property
    def glass_transcript_patterned(self): return GlassTranscriptPatterned
    @property
    def glass_transcript_conserved(self): return GlassTranscriptConserved
    @property
    def glass_transcribed_rna(self): 
        from glasslab.glassatlas.datatypes.transcribed_rna import GlassTranscribedRna
        return GlassTranscribedRna
    @property
    def glass_transcribed_rna_source(self): 
        from glasslab.glassatlas.datatypes.transcribed_rna import GlassTranscribedRnaSource
        return GlassTranscribedRnaSource
    @property
    def peak_feature(self): 
        from glasslab.glassatlas.datatypes.feature import PeakFeature
        return PeakFeature
    @property
    def peak_feature_instance(self):
        from glasslab.glassatlas.datatypes.feature import PeakFeatureInstance 
        return PeakFeatureInstance
    
    def get_transcript_models(self):
        return [self.glass_transcript, self.filtered_glass_transcript,
                self.glass_transcript_source, self.glass_transcript_nucleotides,
                self.glass_transcript_sequence, self.glass_transcript_non_coding,
                self.glass_transcript_patterned, self.glass_transcript_conserved,
                self.glass_transcribed_rna, self.glass_transcribed_rna_source,
                self.peak_feature, self.peak_feature_instance]

    def get_cell_type_base(self, cell_type):
        correlations = self.__class__.get_correlations()
        try: return correlations[cell_type.lower()]
        except KeyError:
            raise Exception('Could not find models to match cell type %s.' % cell_type
                            + '\nOptions are: %s' % ','.join(correlations.keys()))
class TranscriptModelBase(GlassModel):
    cell_base = CellTypeBase()
    class Meta:
        abstract = True
        
class TranscriptionRegionBase(TranscriptModelBase):
    # Use JS for browser link to auto-include in Django Admin form 
    ucsc_session_url = 'http%3A%2F%2Fbiowhat.ucsd.edu%2Fkallison%2Fucsc%2Fsessions%2F'
    ucsc_browser_link_1 = '''<a href="#" onclick="window.open('http://genome.ucsc.edu/cgi-bin/hgTracks?'''\
                        + '''hgS_doLoadUrl=submit&amp;hgS_loadUrlName=%s''' % ucsc_session_url
    ucsc_browser_sess_1 = '''' + (django.jQuery('form')[0].id.match('glasstranscript') && 'glasstranscript' '''\
                        + ''' || 'glasstranscribedrna') + '_' '''\
                        + ''' + (django.jQuery('#id_strand').val()=='0' && 'sense' || 'antisense') + '_strands.txt'''
    ucsc_browser_sess_2 = '''all_tracks.txt'''
    ucsc_browser_link_3 = '''&db=''' + current_settings.REFERENCE_GENOME + '''&amp;position=' + '''\
                        + ''' django.jQuery('#id_chromosome').attr('title') '''\
                        + ''' + '%3A+' + django.jQuery('#id_transcription_start').val() '''\
                        + ''' + '-' + django.jQuery('#id_transcription_end').val(),'Glass Atlas UCSC View ' + '''\
                        + str(randint(100,99999)) + '''); return false;">'''
                        
    ucsc_browser_link = ucsc_browser_link_1 + ucsc_browser_sess_1 + ucsc_browser_link_3\
                        + '''View in UCSC Browser</a> | '''\
                        + ucsc_browser_link_1 + ucsc_browser_sess_2 + ucsc_browser_link_3\
                        + '''All tracks</a> '''
                        
    chromosome              = models.ForeignKey(Chromosome, help_text=ucsc_browser_link)
    strand                  = models.IntegerField(max_length=1, help_text='0 for +, 1 for -')
    transcription_start     = models.IntegerField(max_length=12)
    transcription_end       = models.IntegerField(max_length=12, help_text='<span id="length-message"></span>')
    
    start_end               = BoxField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL box type.')
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return '%s %d: %s: %d-%d' % (self.__class__.__name__, self.id,
                                  self.chromosome.name.strip(), 
                                  self.transcription_start, 
                                  self.transcription_end)
    @classmethod
    def reset_table_name(cls, genome=''):
        '''
        Dynamically reset the current db_table name. Useful for 
        switching between test DBs.
        '''
        cls._meta.db_table = 'glass_atlas_%s_%s"."glass_transcript' % (
                                genome or current_settings.TRANSCRIPT_GENOME, 
                                cls.cell_base.cell_type.lower())
        
    @classmethod 
    def add_from_tags(cls,  tag_table):
        connection.close()
        sequencing_run = SequencingRun.objects.get(source_table=tag_table)
        if not sequencing_run.standard: 
            raise Exception('This is not a table marked as "standard," and will not be added to the transcript set.')
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
        for model in cls.cell_base.get_transcript_models():
            execute_query_without_transaction('VACUUM FULL ANALYZE "%s";' % (model._meta.db_table))
        
        # Multiprocessing locks for some reason; do each separately.
        #for chr_list in current_settings.CHR_LISTS:
        #    wrap_force_vacuum(cls, chr_list)
    
    @classmethod        
    def _force_vacuum(cls, chr_list):
        for chr_id in chr_list:
            execute_query_without_transaction('VACUUM FULL ANALYZE "%s_%d";' % (
                                                                    cls.cell_base.glass_transcript._meta.db_table, 
                                                                    chr_id))
            
            execute_query_without_transaction('VACUUM FULL ANALYZE "%s_%d";' % (
                                                                    cls.cell_base.glass_transcript_prep._meta.db_table, 
                                                                    chr_id))

    @classmethod
    def toggle_autovacuum(cls, on=True):
        '''
        Toggle per-table autovacuum enabled state.
        '''
        for model in cls.cell_base.get_transcript_models():
            execute_query('ALTER TABLE "%s" SET (autovacuum_enabled=%s);' \
                    % (model._meta.db_table, on and 'true' or 'false'))
            
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
            
class TranscriptBase(TranscriptionRegionBase):
    '''
    Unique transcribed regions in the genome, as determined via GRO-Seq.
    '''   
    class Meta:
        abstract = True
        
class GlassTranscriptPrep(TranscriptBase):
    processed               = models.NullBooleanField(default=None, help_text='Do we have RNA-Seq confirmation?')
    
    class Meta:
        abstract    = True

class GlassTranscript(TranscriptBase):
    density             = models.FloatField(null=True)
    start_end_density   = BoxField(null=True, default=None, help_text='This is a placeholder for the PostgreSQL box type.')
    
    spliced             = models.NullBooleanField(default=None, help_text='Do we have RNA-Seq confirmation?')
    score               = models.FloatField(null=True, default=None)
    
    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract    = True
          
    ################################################
    # GRO-Seq to transcripts
    ################################################
    @classmethod 
    def add_transcripts_from_groseq(cls,  tag_table, sequencing_run):
        multiprocess_glass_tags(wrap_add_transcripts_from_groseq, cls, sequencing_run)
         
    @classmethod
    def _add_transcripts_from_groseq(cls, chr_list, sequencing_run):
        for chr_id in chr_list:
            print 'Adding transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s_prep.save_transcripts_from_sequencing_run(%d, %d,'%s', %d, %d, %d, %d, %d, NULL, NULL);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       sequencing_run.id, chr_id, 
                       sequencing_run.source_table.strip(), 
                       MAX_GAP, TAG_EXTENSION, 
                       MAX_EDGE, EDGE_SCALING_FACTOR, DENSITY_MULTIPLIER)
            execute_query(query)

    @classmethod 
    def remove_rogue_run(cls):
        multiprocess_glass_tags(wrap_remove_rogue_run, cls)
   
    @classmethod
    def _remove_rogue_run(cls, chr_list):
        for chr_id in chr_list:
            print 'Removing rogue transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s_prep.remove_rogue_run(%d, %d, %d, %d, %d, %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       chr_id, MAX_GAP, TAG_EXTENSION, 
                       MAX_EDGE, EDGE_SCALING_FACTOR, DENSITY_MULTIPLIER)
            execute_query(query)
    
    ################################################
    # Transcript cleanup and refinement
    ################################################
    @classmethod
    def stitch_together_transcripts(cls, allow_extended_gaps=True):
        multiprocess_all_chromosomes(wrap_stitch_together_transcripts, cls, allow_extended_gaps)
        #wrap_stitch_together_transcripts(cls,[21, 22])
    
    @classmethod
    def _stitch_together_transcripts(cls, chr_list, allow_extended_gaps=True):
        '''
        This is tag-level agnostic, stitching based on gap size alone.
        '''
        for chr_id  in chr_list:
            print 'Stitching together transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s_prep.save_transcripts_from_existing(%d, %d);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       chr_id, MAX_STITCHING_GAP)
            execute_query(query)
            print 'Setting average tags for preparatory transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s_prep.set_density(%d, %d, %d, %d, %s, %s);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       chr_id, MAX_EDGE, EDGE_SCALING_FACTOR, 
                       DENSITY_MULTIPLIER, 
                       allow_extended_gaps and 'true' or 'false', 'false')
            execute_query(query)
    
    @classmethod
    def set_density(cls, allow_extended_gaps=True):
        multiprocess_all_chromosomes(wrap_set_density, cls, allow_extended_gaps)
    
    @classmethod
    def _set_density(cls, chr_list, allow_extended_gaps=True):
        '''
        Force reset average tags for prep DB.
        '''
        for chr_id  in chr_list:
            print 'Setting average tags for preparatory transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s_prep.set_density(%d, %d, %d, %d, %s, %s);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       chr_id, MAX_EDGE, EDGE_SCALING_FACTOR, 
                       DENSITY_MULTIPLIER,
                       allow_extended_gaps and 'true' or 'false', 'true')
            execute_query(query)
            
    @classmethod
    def draw_transcript_edges(cls):
        multiprocess_all_chromosomes(wrap_draw_transcript_edges, cls)
        #wrap_stitch_together_transcripts(cls,[21, 22])
    
    @classmethod
    def _draw_transcript_edges(cls, chr_list):
        for chr_id in chr_list:
            print 'Drawing edges for transcripts for chromosome %d' % chr_id
            query = """
                -- @todo: delete existing tables?
                SELECT glass_atlas_%s_%s.draw_transcript_edges(%d);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       chr_id)
            execute_query(query)
            print 'Setting average tags for transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s.set_density(%d, %d, %s);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       chr_id, DENSITY_MULTIPLIER, 'true')
            execute_query(query)
            
    @classmethod
    def set_score_thresholds(cls, sample_count=500, sample_size=100, allow_zero=False):
        multiprocess_all_chromosomes(wrap_set_score_thresholds, cls, sample_count, sample_size, allow_zero)
    
    @classmethod
    def _set_score_thresholds(cls, chr_list, sample_count=500, sample_size=100, allow_zero=False):
        '''
        Randomly sample, for all standard tables, expected tag counts by chromosome and
        strand. Store expected tag counts.
        
        If allow_zero = True, regions of zero tags are included in the sample average.
        (By default, regions with zero tags are omitted.)
        
        sample_count # Number of samples to take from each run
        sample_size # Sample size in bp
        
        Note that transcription start and end are inclusive, so length = end - start + 1.
        
        Note that sample_count + 2% samples are kept, with the bottom and top 1% thrown out. 
        '''
        for chr_id in chr_list:
            connection.close()
            
            print 'Setting score threshold for chromosome %d' % chr_id
            # First, set up regions in each chr to sample.
            chr = Chromosome.objects.get(id=chr_id)
            position_range = chr.length - 1
            
            runs_to_sample = 3
            runs = list(SequencingRun.objects.filter(type='Gro-Seq', standard=True))
            # Get all samples
            for strand in (0,1):
                tag_counts = []
                for i, run in enumerate(sample(runs, runs_to_sample)):
                    connection.close()
                    acquired = 0
                    while acquired < (sample_count + .02*sample_count):
                        start = randint(0,position_range - sample_size + 1)
                        query = """
                            SELECT count(id) FROM "%s_%d" 
                            WHERE strand = %d
                            AND start_end <@ public.make_box(%d, 0, %d, 0);
                            """ % (run.source_table.strip(), chr_id, strand, start, (start + sample_size - 1))
                        count = fetch_rows(query)[0][0]
                        if count > 0 or allow_zero:
                            tag_counts.append(count)
                            acquired += 1
                            
                # Cut out top and bottom 1%
                total_counts = len(tag_counts)
                tag_counts.sort()
                tag_counts = tag_counts[int(.01*total_counts):(int(.01*total_counts) + total_counts)]
                    
                average = sum(tag_counts)/len(tag_counts)
                record, created = ExpectedTagCount.objects.get_or_create(chromosome=chr, strand=strand)
                record.sample_count = sample_count
                record.sample_size = sample_size
                record.tag_count = average
                record.save()
            
    @classmethod
    def set_scores(cls):
        multiprocess_all_chromosomes(wrap_set_scores, cls)
        #wrap_set_scores(cls,[21, 22])
    
    @classmethod
    def _set_scores(cls, chr_list):
        for chr_id in chr_list:
            print 'Scoring transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s.calculate_scores(%d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(), chr_id)
            execute_query(query) 
    @classmethod
    def mark_as_spliced(cls):
        multiprocess_all_chromosomes(wrap_mark_as_spliced, cls)
        #wrap_set_scores(cls,[21, 22])
    
    @classmethod
    def _mark_as_spliced(cls, chr_list):
        from glasslab.glassatlas.datatypes.transcribed_rna import MIN_SCORE_RNA
        for chr_id in chr_list:
            print 'Marking transcripts as spliced for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s.mark_transcripts_spliced(%d, %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(), chr_id, 
                       MIN_SCORE_RNA)
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
            
            nucleotides_model = cls.cell_base.glass_transcript_nucleotides
            for transcript in cls.objects.filter(chromosome__id=chr_id, score__isnull=True):
                start = transcript.transcription_start
                stop = transcript.transcription_end
                beginning = fasta[start//length][start % length - 1:]
                end = fasta[stop//length][:stop % length]
                middle = fasta[(start//length + 1):(stop//length)]
                seq = (beginning + ''.join(middle) + end).upper()
                try: sequence = nucleotides_model.objects.get(glass_transcript=transcript)
                except nucleotides_model.DoesNotExist:
                    sequence = nucleotides_model(glass_transcript=transcript)
                sequence.sequence = seq
                sequence.save()
            connection.close()
            
    @classmethod
    def mark_all_reloaded(cls):
        '''
        Mark all transcripts as reloaded. Called by external processes that have reloaded runs appropriately.
        '''
        connection.close()
        cls.objects.all().update(requires_reload=False)
    
class FilteredGlassTranscriptManager(models.Manager):
    def get_query_set(self):
        return super(FilteredGlassTranscriptManager, self).get_query_set().filter(score__gte=MIN_SCORE)
    
class FilteredGlassTranscript(object):
    '''
    Acts as a grouping of shared methods for filtered glass transcripts.
    Not a model because the proxy models that will inherit these methods
    complain if they inherit from an abstract method.
    '''
    objects = FilteredGlassTranscriptManager()
    
    ################################################
    # Visualization
    ################################################
    @classmethod
    def generate_bed_file(cls, output_dir):
        '''
        Generates a BED file (http://genome.ucsc.edu/FAQ/FAQformat.html#format1)
        of all the transcripts and their exons for viewing in the UCSC Genome Browser.
        '''
        
        max_score = cls.objects.aggregate(max=Max('score'))['max']
        transcripts = cls.objects.order_by('chromosome__id','transcription_start')
        cls._generate_bed_file(output_dir, transcripts, max_score, strand=0)
        cls._generate_bed_file(output_dir,transcripts, max_score, strand=1)
        
    @classmethod
    def _generate_bed_file(cls, output_dir, transcripts, max_score, strand=0):
        file_name = 'Glass_Transcripts_%s_%d.bed' % (datetime.now().strftime('%Y_%m_%d'), strand)
        file_path = os.path.join(output_dir, file_name)
        
        transcripts = transcripts.filter(strand=strand)
        
        strand_char = strand and '-' or '+'
        output = 'track name=glass_transcripts_%d description="Glass Atlas Transcripts %s strand" useScore=1 itemRgb=On\n' \
                        % (strand, strand_char)
        
        for trans in transcripts:
            # chrom start end name score strand thick_start thick_end colors? exon_count csv_exon_sizes csv_exon_starts
            start = max(0,trans.transcription_start)
            end = min(trans.chromosome.length - 1,trans.transcription_end)
            row = [trans.chromosome.name, str(start), str(end), 
                   'Transcript_' + str(trans.id), str((float(trans.score)/max_score)*1000),
                   trans.strand and '-' or '+', str(start), str(end), 
                   trans.strand and '0,255,0' or '0,0,255']
            
            # Add in exons
            # Note: 1 bp start and end exons added because UCSC checks that start and end of 
            # whole transcript match the start and end of the first and last blocks, respectively
            exons = cls.cell_base.glass_transcribed_rna.objects.filter(glass_transcript=trans
                                    ).annotate(tags=Sum('glasstranscribedrnasource__tag_count')
                                    ).filter(tags__gt=1).order_by('transcription_start')
            row += [str(exons.count() + 2),
                    ','.join(['1'] +
                             [str(min(trans.transcription_end - ex.transcription_start,
                                ex.transcription_end - ex.transcription_start)) for ex in exons] + ['1']),
                    ','.join(['0'] +
                             [str(max(0, ex.transcription_start - trans.transcription_start)) for ex in exons] 
                                + [str(end - start - 1)]),
                    ]
        
            output += '\t'.join(row) + '\n'
        
        f = open(file_path, 'w')
        f.write(output)
        f.close()
        
            
          
class GlassTranscriptNucleotides(TranscriptModelBase):
    sequence          = models.TextField()
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return 'GlassTranscriptNucleotides for transcript %d' % (self.glass_transcript.id)
       

class TranscriptSourceBase(TranscriptModelBase):
    sequencing_run          = models.ForeignKey(SequencingRun)
    tag_count               = models.IntegerField(max_length=12)
    polya_count               = models.IntegerField(max_length=12)
    gaps                    = models.IntegerField(max_length=12)
    #polya_count             = models.IntegerField(max_length=12)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return '%s: %d tags from %s' % (self.__class__.__name__,
                                          self.tag_count,
                                          self.sequencing_run.source_table.strip())
        
class GlassTranscriptSourcePrep(TranscriptSourceBase):
    class Meta:
        abstract = True

class GlassTranscriptSource(TranscriptSourceBase):
    class Meta:
        abstract = True
        
class GlassTranscriptTranscriptionRegionTable(TranscriptModelBase):
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
        
class GlassTranscriptSequence(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the sequence record it maps to.
    '''
    sequence_transcription_region   = models.ForeignKey(SequenceTranscriptionRegion)
    
    table_type = 'sequence'
    related_class = SequenceTranscriptionRegion
    
    class Meta: 
        abstract = True
           
class GlassTranscriptNonCoding(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the non coding region it maps to.
    '''
    non_coding_transcription_region = models.ForeignKey(NonCodingTranscriptionRegion)
    
    table_type = 'non_coding'
    related_class = NonCodingTranscriptionRegion

    class Meta: 
        abstract = True
        
class GlassTranscriptPatterned(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the patterned region it maps to.
    '''
    patterned_transcription_region  = models.ForeignKey(PatternedTranscriptionRegion)
    
    table_type      = 'patterned'
    related_class   = PatternedTranscriptionRegion
    
    class Meta: 
        abstract = True
        
class GlassTranscriptConserved(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the conservation region it maps to.
    '''
    conserved_transcription_region  = models.ForeignKey(ConservedTranscriptionRegion)
    
    table_type      = 'conserved'
    related_class   = ConservedTranscriptionRegion

    class Meta: 
        abstract = True
    