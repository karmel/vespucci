'''
Created on Nov 8, 2010

@author: karmel
'''
from __future__ import division
from glasslab.config import current_settings
from django.db import models, connection, utils
from glasslab.utils.datatypes.genome_reference import Chromosome,\
    SequenceTranscriptionRegion, PatternedTranscriptionRegion,\
    ConservedTranscriptionRegion, NonCodingTranscriptionRegion,\
    DupedTranscriptionRegion
from glasslab.glassatlas.datatypes.metadata import SequencingRun
from glasslab.utils.datatypes.basic_model import BoxField, GlassModel
from multiprocessing import Pool
from glasslab.utils.database import execute_query,\
    execute_query_without_transaction, fetch_rows
import os
from random import randint
from django.db.models.aggregates import Max
from datetime import datetime
import traceback

# The tags returned from the sequencing run are shorter than we know them to be biologically
# We can therefore extend the mapped tag region by a set number of bp if an extension is passed in
TAG_EXTENSION = 0

MAX_GAP = 0 # Max gap between transcripts from the same run
MAX_STITCHING_GAP = MAX_GAP # Max gap between transcripts being stitched together
MAX_EDGE = 20 # Max edge length of transcript graph subgraphs to be created
EDGE_SCALING_FACTOR = 20 # Number of transcripts per DENSITY_MULTIPLIER bp required to get full allowed edge length
DENSITY_MULTIPLIER = 1000 # Scaling factor on density-- think of as bps worth of tags to consider
MIN_SCORE = 6 # Hide transcripts with scores below this threshold.

def multiprocess_all_chromosomes(func, cls, *args, **kwargs):
    ''' 
    Convenience method for splitting up queries based on glass tag id.
    '''
    processes = current_settings.ALLOWED_PROCESSES
    p = Pool(processes)
    
    if not current_settings.CHR_LISTS:
        try:
            try:
                # Note that we accept a kwarg use_table
                all_chr = fetch_rows('''
                    SELECT chromosome_id as id
                    FROM "%s" 
                    GROUP BY chromosome_id ORDER BY COUNT(chromosome_id) DESC;''' 
                                    % (kwargs.get('use_table',None) or cls._meta.db_table))
            except utils.DatabaseError:
                # Prep table instead?
                all_chr = fetch_rows('''
                    SELECT chromosome_id as id
                    FROM "%s" 
                    GROUP BY chromosome_id ORDER BY COUNT(chromosome_id) DESC;''' 
                                    % (getattr(cls,'prep_table',None)
                                        or cls.cell_base.glass_transcript_prep._meta.db_table))
                
            all_chr = zip(*all_chr)[0]
            if not all_chr: raise Exception
            
        except Exception:
            # cls in question does not have explicit relation to chromosomes; get all
            all_chr = current_settings.GENOME_CHROMOSOMES

        # Chromosomes are sorted by count descending, so we want to snake them
        # back and forth to create even-ish groups. 
        chr_sets = [[] for _ in xrange(0, processes)]
        for i,chrom in enumerate(all_chr):
            if i and not i % processes: chr_sets.reverse()
            chr_sets[i % processes].append(chrom)
        
        # Reverse every other group to even out memory requirements.
        for i, chr_set in enumerate(chr_sets):
            if i % 2 == 0: chr_set.reverse()
            
        current_settings.CHR_LISTS = chr_sets
        print 'Determined chromosome sets:\n%s' % str(current_settings.CHR_LISTS)
    
    for chr_list in current_settings.CHR_LISTS:
        p.apply_async(func, args=[cls, chr_list,] + list(args))
    p.close()
    p.join()

# The following methods wrap bound methods. This is necessary
# for use with multiprocessing. Note that getattr with dynamic function names
# doesn't seem to work either.
def wrap_errors(func, *args):
    try: func(*args)
    except Exception:
        print 'Encountered exception in wrapped function:\n%s' % traceback.format_exc()
        raise
   
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
        from glasslab.glassatlas.datatypes.celltypes.bmdc import BMDCBase
        return {'thiomac': ThioMacBase, 'bmdc':BMDCBase}
          
    @property
    def glass_transcript(self): return GlassTranscript
    @property
    def glass_transcript_prep(self): return GlassTranscriptPrep
    @property
    def filtered_glass_transcript(self): return FilteredGlassTranscript
    @property
    def glass_transcript_source(self): return GlassTranscriptSource
    @property
    def glass_transcript_source_prep(self): return GlassTranscriptSourcePrep
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
    def peak_feature(self): 
        from glasslab.glassatlas.datatypes.feature import PeakFeature
        return PeakFeature
    
    def get_transcript_models(self):
        return [self.glass_transcript, self.glass_transcript_prep, 
                self.glass_transcript_source, self.glass_transcript_source_prep, 
                self.glass_transcript_nucleotides,
                self.glass_transcript_sequence, self.glass_transcript_non_coding,
                self.glass_transcript_patterned, self.glass_transcript_conserved,
                self.peak_feature]

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
                        
    ucsc_browser_link = ucsc_browser_link_1 + ucsc_browser_sess_2 + ucsc_browser_link_3\
                        + '''View in UCSC Browser</a>'''
                        
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
        cls._meta.db_table = 'glass_atlas_%s_%s%s"."glass_transcript' % (
                                genome or current_settings.TRANSCRIPT_GENOME, 
                                cls.cell_base.cell_type.lower(),
                                current_settings.STAGING)
        
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
            execute_query_without_transaction('VACUUM ANALYZE "%s";' % (model._meta.db_table))
        
    @classmethod
    def force_vacuum_prep(cls):
        '''
        VACUUM ANALYZE prep tables.
        '''
        print 'Vacuum analyzing prep tables.'
        for model in [cls.cell_base.glass_transcript_prep, cls.cell_base.glass_transcript_source_prep]:
            execute_query_without_transaction('VACUUM ANALYZE "%s";' % (model._meta.db_table))
        multiprocess_all_chromosomes(wrap_force_vacuum, cls)
        
    @classmethod        
    def _force_vacuum(cls, chr_list):
        for chr_id in chr_list:
            print 'Vacuum analyzing chromosome partitions for chr %d' % chr_id
            execute_query_without_transaction('VACUUM ANALYZE "%s_%d";' % (
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
    refseq              = models.BooleanField(help_text='Does this transcript overlap with RefSeq transcripts (strand-specific)?')
    
    class Meta:
        abstract = True
        
class GlassTranscriptPrep(TranscriptBase):
    
    class Meta:
        abstract    = True

class GlassTranscript(TranscriptBase):
    distal              = models.BooleanField(help_text='Is this transcript at least 1000 bp away from RefSeq transcripts (not strand-specific)?')
    spliced             = models.NullBooleanField(default=None, help_text='Do we have RNA-Seq confirmation?')
    standard_error      = models.FloatField(null=True, default=None)
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
        multiprocess_all_chromosomes(wrap_add_transcripts_from_groseq, cls, 
                                     sequencing_run, use_table=tag_table)
         
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
            query = '''
            INSERT INTO gr_project_2012.tag_count_per_basepair
            (glass_transcript_id, sequencing_run_id, 
                basepair, tag_count, tag_start) 
            SELECT glass_transcript_id, {0}, basepair, sum(tag_count), true
            FROM (SELECT t.glass_transcript_id, 
                (CASE WHEN t.strand = 1 THEN t.transcription_end - tag."end"
                    ELSE tag.start - t.transcription_start END) as basepair, 
                count(tag.id) as tag_count
                FROM gr_project_2012.glass_transcript_start t
                JOIN "{1}_{2}" tag
                ON  t.start_end && tag.start_end
                AND t.strand = tag.strand
                WHERE t.chromosome_id = {2}
            group by t.id, t.strand, t.transcription_start, tag.start, t.transcription_end, tag."end"
            ) der
            group by glass_transcript_id, basepair;
            '''.format(sequencing_run.id, sequencing_run.source_table, chr_id)

            execute_query(query)
            

    
    ################################################
    # Transcript cleanup and refinement
    ################################################
    @classmethod
    def stitch_together_transcripts(cls, allow_extended_gaps=True, set_density=False, null_only=True):
        multiprocess_all_chromosomes(wrap_stitch_together_transcripts, cls, 
                                     allow_extended_gaps, set_density, null_only)
    
    @classmethod
    def _stitch_together_transcripts(cls, chr_list, allow_extended_gaps=True, set_density=False, null_only=True):
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
            if set_density:
                print 'Setting average tags for preparatory transcripts for chromosome %d' % chr_id
                query = """
                    SELECT glass_atlas_{0}_{1}_prep.set_density({2},{3},{4},{5},{6},{7});
                    """.format(current_settings.TRANSCRIPT_GENOME, 
                               current_settings.CURRENT_CELL_TYPE.lower(),
                               chr_id, MAX_EDGE, EDGE_SCALING_FACTOR, 
                               DENSITY_MULTIPLIER, 
                               allow_extended_gaps and 'true' or 'false',
                               null_only and 'true' or 'false')
                execute_query(query)
    
    @classmethod
    def set_density(cls, allow_extended_gaps=True, null_only=True):
        multiprocess_all_chromosomes(wrap_set_density, cls, allow_extended_gaps, null_only)
    
    @classmethod
    def _set_density(cls, chr_list, allow_extended_gaps=True, null_only=True):
        '''
        Force reset average tags for prep DB.
        '''
        for chr_id  in chr_list:
            print 'Setting average tags for preparatory transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_{0}_{1}_prep.set_density({2},{3},{4},{5},{6},{7});
                """.format(current_settings.TRANSCRIPT_GENOME, 
                           current_settings.CURRENT_CELL_TYPE.lower(),
                           chr_id, MAX_EDGE, EDGE_SCALING_FACTOR, 
                           DENSITY_MULTIPLIER, 
                           allow_extended_gaps and 'true' or 'false',
                           null_only and 'true' or 'false')
            execute_query(query)
            
    @classmethod
    def draw_transcript_edges(cls):
        multiprocess_all_chromosomes(wrap_draw_transcript_edges, cls)
        
    @classmethod
    def _draw_transcript_edges(cls, chr_list):
        for chr_id in chr_list:
            print 'Drawing edges for transcripts for chromosome %d' % chr_id
            query = """
                SELECT glass_atlas_%s_%s%s.draw_transcript_edges(%d);
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       current_settings.STAGING,
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
                SELECT glass_atlas_%s_%s%s.calculate_scores(%d);
                SELECT glass_atlas_%s_%s%s.calculate_standard_error(%d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       current_settings.STAGING, chr_id,
                       current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       current_settings.STAGING, chr_id)
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
                SELECT glass_atlas_%s_%s%s.mark_transcripts_spliced(%d, %d);
                """ % (current_settings.TRANSCRIPT_GENOME,
                       current_settings.CURRENT_CELL_TYPE.lower(),
                       current_settings.STAGING, chr_id, 
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
        output = ('track name=glass_transcripts_{0} description=' \
                    + '"Glass Atlas Transcripts {1} strand" useScore=1 itemRgb=On\n').format(strand, strand_char)
        
        for trans in transcripts:
            # chrom start end name score strand thick_start thick_end colors? exon_count csv_exon_sizes csv_exon_starts
            # Make sure we don't go beyond the length of the chromosome.
            # Transcripts shouldn't due to previous processing, but just in case, we check here as well.
            start = max(0,trans.transcription_start)
            end = min(trans.chromosome.length,trans.transcription_end)
            row = [trans.chromosome.name, str(start), str(end), 
                   'Transcript_' + str(trans.id), str((float(trans.score)/max_score)*1000),
                   trans.strand and '-' or '+', str(start), str(end), 
                   trans.strand and '0,255,0' or '0,0,255']
            
            '''
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
                             [str(max(1, ex.transcription_start - trans.transcription_start)) for ex in exons] 
                                + [str(end - start - 1)]),
                    ]
            '''
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
    gaps                    = models.IntegerField(max_length=12)
    
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
        
class GlassTranscriptInfrastructure(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the infrastructural ncRNA it maps to.
    '''
    infrastructure_transcription_region  = models.ForeignKey(PatternedTranscriptionRegion)
    
    table_type      = 'infrastructure'
    related_class   = PatternedTranscriptionRegion
    
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
        
class GlassTranscriptDuped(GlassTranscriptTranscriptionRegionTable):
    '''
    Relationship between GlassTranscript and the segmental dupes region it maps to.
    '''
    duped_transcription_region  = models.ForeignKey(DupedTranscriptionRegion)
    
    table_type      = 'duped'
    related_class   = DupedTranscriptionRegion
    
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
    