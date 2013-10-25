'''
Created on Nov 8, 2010

@author: karmel
'''
from __future__ import division
from vespucci.config import current_settings
from django.db import models, connection, utils
from vespucci.genomereference.datatypes import Chromosome,\
    SequenceTranscriptionRegion, NonCodingTranscriptionRegion,\
    SequencingRun
from vespucci.utils.datatypes.basic_model import Int8RangeField, VespucciModel
from multiprocessing import Pool
from vespucci.utils.database import execute_query, fetch_rows,\
    commit_transaction, rollback_transaction, execute_query_in_transaction,\
    execute_query_without_transaction, get_cursor
import os
from django.db.models.aggregates import Max
from datetime import datetime
import traceback
from django.db.transaction import commit_manually

# The tags returned from the sequencing run are shorter 
# than we know them to be biologically
# We can therefore extend the mapped tag region by a set number 
# of bp if an extension is passed in
TAG_EXTENSION = 0

# Max gap between transcripts from the same run
MAX_GAP = 0
# Max gap between transcripts being stitched together
MAX_STITCHING_GAP = MAX_GAP
# Number of tags per DENSITY_MULTIPLIER bp to get full allowed edge length
EDGE_SCALING_FACTOR = 5
# Tags in transcripts that only appear in one run must be 
# greater than this to be included in edge drawing
MIN_ONE_RUN_TAGS = 3
# Hide transcripts with scores below this threshold. 
MIN_SCORE = 1


def set_chromosome_lists(cls, use_table=None):
    '''
    Get and set available chromosomes to multiprocess.
    '''
    if not current_settings.CHR_LISTS:
        processes = current_settings.ALLOWED_PROCESSES
        try:
            try:
                # Note that we accept a kwarg use_table
                all_chr = fetch_rows('''
                    SELECT chromosome_id as id
                    FROM "{0}" 
                    GROUP BY chromosome_id 
                    ORDER BY COUNT(chromosome_id) DESC;'''.format(
                                    use_table or cls._meta.db_table))
            except utils.DatabaseError:
                # Prep table instead?
                all_chr = fetch_rows('''
                    SELECT chromosome_id as id
                    FROM "{0}" 
                    GROUP BY chromosome_id 
                    ORDER BY COUNT(chromosome_id) DESC;'''.format(
                        getattr(cls,'prep_table',None)
                        or cls.cell_base.atlas_transcript_prep._meta.db_table))
                
            all_chr = zip(*all_chr)[0]
            if not all_chr: raise Exception
            
        except Exception:
            # cls in question does not have relation to chromosomes; get all
            all_chr = current_settings.GENOME_CHOICES[current_settings.GENOME]['chromosomes']
        
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
        print 'Determined chromosome sets:\n{0}'.format(
                                        str(current_settings.CHR_LISTS))
    

def multiprocess_all_chromosomes(func, cls, *args, **kwargs):
    ''' 
    Convenience method for splitting up queries based on tag id.
    '''
    processes = current_settings.ALLOWED_PROCESSES
    
    set_chromosome_lists(cls, use_table=kwargs.get('use_table',None))
    print args
    p = Pool(processes)
    
    try:
        for chr_list in current_settings.CHR_LISTS:
            print [cls, chr_list,] + list(args)
            p.apply_async(func, args=[cls, chr_list,] + list(args))            
        p.close()
        p.join()
    except Exception, e:
        print 'Terminating pool.'
        p.terminate()
        raise e

# The following methods wrap bound methods. This is necessary
# for use with multiprocessing. Note that getattr with dynamic function names
# doesn't seem to work either.
def wrap_errors(func, *args):
    try: func(*args)
    except Exception, e:
        print 'Encountered exception in wrapped function:\n{0}'.format(
                                                    traceback.format_exc())
        raise e
   
def wrap_add_transcripts_from_groseq(cls, chr_list, *args): 
    wrap_errors(cls._add_transcripts_from_groseq, chr_list, *args)
def wrap_stitch_together_transcripts(cls, chr_list, *args): 
    wrap_errors(cls._stitch_together_transcripts, chr_list, *args)
def wrap_set_density(cls, chr_list, *args): 
    wrap_errors(cls._set_density, chr_list, *args)
def wrap_draw_transcript_edges(cls, chr_list): 
    wrap_errors(cls._draw_transcript_edges, chr_list)
def wrap_set_scores(cls, chr_list, *args): 
    wrap_errors(cls._set_scores, chr_list, *args)
def wrap_force_vacuum(cls, chr_list): 
    wrap_errors(cls._force_vacuum, chr_list)

class CellTypeBase(object):
    cell_type = ''
    
    @classmethod
    def get_correlations(cls):
        '''
        This is where you add in custom cell type classes if desired.
        CD4TCell is provided as an example.
        '''
        from vespucci.atlas.datatypes.celltypes.cd4tcell import CD4TCellBase
        from vespucci.atlas.datatypes.celltypes.default import DefaultBase
        return {'default': DefaultBase,
                'cd4tcell': CD4TCellBase,}
      
    @property
    def atlas_transcript(self): return AtlasTranscript
    @property
    def atlas_transcript_prep(self): return AtlasTranscriptPrep
    @property
    def filtered_atlas_transcript(self): return FilteredAtlasTranscript
    @property
    def atlas_transcript_source(self): return AtlasTranscriptSource
    @property
    def atlas_transcript_source_prep(self): return AtlasTranscriptSourcePrep
    @property
    def atlas_transcript_sequence(self): return AtlasTranscriptSequence
    @property
    def atlas_transcript_non_coding(self): return AtlasTranscriptNonCoding

    
    def get_transcript_models(self):
        return [self.atlas_transcript, self.atlas_transcript_prep, 
                self.atlas_transcript_source, self.atlas_transcript_source_prep, 
                self.atlas_transcript_sequence, self.atlas_transcript_non_coding]

    def get_cell_type_base(self, cell_type, fail_if_not_found=False):
        correlations = self.__class__.get_correlations()
        try: 
            cell_base = correlations[cell_type.lower()]
            current_settings.CELL_TYPE = cell_base.cell_type.lower()
            return cell_base
        except KeyError:
            if fail_if_not_found:
                raise Exception('Cell type {} not recognized.'.format(cell_type)
                            + '\nOptions are: {}'.format(
                                                ','.join(correlations.keys())))
                
            # We want to use the Default template models,
            # But we reload here to ensure all db_tables are correct
            current_settings.CELL_TYPE = cell_type.lower()
            from vespucci.atlas.datatypes.celltypes import default
            reload(default)
            return default.DefaultBase
            
class TranscriptModelBase(VespucciModel):
    cell_base = CellTypeBase()
    schema_base = 'atlas_{0}_{1}'
    class Meta(object):
        abstract = True
        
class TranscriptionRegionBase(TranscriptModelBase):
                       
    chromosome = models.ForeignKey(Chromosome)
    strand = models.IntegerField(max_length=1, help_text='0 for +, 1 for -')
    transcription_start = models.IntegerField(max_length=12)
    transcription_end = models.IntegerField(max_length=12)
    
    start_end = Int8RangeField(null=True, default=None)
    
    class Meta(object):
        abstract = True
    
    def __unicode__(self):
        return '{0} {1}: {2}: {3}-{4}'.format(self.__class__.__name__, self.id,
                                  self.chromosome.name.strip(), 
                                  self.transcription_start, 
                                  self.transcription_end)

        
    @classmethod 
    def add_from_tags(cls,  tag_table):
        connection.close()
        sequencing_run = SequencingRun.objects.get(source_table=tag_table)
        cls.add_transcripts_from_groseq(tag_table, sequencing_run)
            
                
class TranscriptBase(TranscriptionRegionBase):
    '''
    Unique transcribed regions in the genome, as determined via GRO-Seq.
    '''   
    refseq = models.BooleanField(help_text='Does this transcript overlap ' \
                            + ' with RefSeq transcripts (strand-specific)?')
    
    class Meta(object):
        abstract = True
        
class AtlasTranscriptPrep(TranscriptBase):
    
    class Meta(object):
        abstract    = True

class AtlasTranscript(TranscriptBase):
    distal = models.BooleanField(help_text='Is this transcript at least 1000' \
                    + ' bp away from RefSeq transcripts (not strand-specific)?')
    standard_error = models.FloatField(null=True, default=None)
    score = models.FloatField(null=True, default=None)
    rpkm = models.FloatField(null=True, default=None)
    
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta(object):
        abstract    = True
          
    ################################################
    # GRO-Seq to transcripts
    ################################################
    @classmethod 
    def add_transcripts_from_groseq(cls,  tag_table, sequencing_run):
        try:
            set_chromosome_lists(cls, use_table=tag_table)
            multiprocess_all_chromosomes(wrap_add_transcripts_from_groseq, cls, 
                                         sequencing_run, use_table=tag_table)
        except Exception, e:
            raise e
         
    @classmethod
    def _add_transcripts_from_groseq(cls, chr_list, sequencing_run):
        try:
            for chr_id in chr_list:
                print 'Adding transcripts for chromosome %d' % chr_id
                query = """
                    SELECT atlas_{}_{}_prep.save_transcripts_from_sequencing_run(
                        {}, {}, '{}', {}, {}, {}, {}, {}, NULL, NULL);
                    """.format(current_settings.GENOME,
                               current_settings.CELL_TYPE.lower(),
                               sequencing_run.id, 
                               chr_id, 
                               sequencing_run.source_table.strip(), 
                               MAX_GAP, 
                               TAG_EXTENSION, 
                               current_settings.MAX_EDGE, 
                               EDGE_SCALING_FACTOR, 
                               current_settings.DENSITY_MULTIPLIER)
                execute_query(query)
        except Exception, e:
            raise e
    
    ################################################
    # Transcript cleanup and refinement
    ################################################
    @classmethod
    def stitch_together_transcripts(cls, 
                                    allow_extended_gaps=True, 
                                    extension_percent='.2', 
                                    set_density=False, 
                                    null_only=True):
        try:
            set_chromosome_lists(cls)
            multiprocess_all_chromosomes(wrap_stitch_together_transcripts, 
                                         cls, 
                                         allow_extended_gaps, 
                                         extension_percent, 
                                         set_density, 
                                         null_only)
        except Exception, e:
            raise e
    
    @classmethod
    def _stitch_together_transcripts(cls, chr_list, 
                                     allow_extended_gaps=True, 
                                     extension_percent='.2', 
                                     set_density=False, 
                                     null_only=True):
        '''
        This is tag-level agnostic, stitching based on gap size alone.
        '''
        try:
            for chr_id  in chr_list:
                print 'Stitching together transcripts for chr_id %d' % chr_id
                query = """
                    SELECT atlas_{}_{}_prep.save_transcripts_from_existing({}, {});
                    """.format(current_settings.GENOME, 
                               current_settings.CELL_TYPE.lower(),
                               chr_id, 
                               MAX_STITCHING_GAP)
                execute_query(query)
                if set_density:
                    print 'Setting density for transcripts for chr_id %d' % chr_id
                    query = """
                        SELECT atlas_{}_{}_prep.set_density({},{},{},{},{},{},{});
                        """.format(current_settings.GENOME, 
                                   current_settings.CELL_TYPE.lower(),
                                   chr_id, 
                                   current_settings.MAX_EDGE, 
                                   EDGE_SCALING_FACTOR, 
                                   current_settings.DENSITY_MULTIPLIER, 
                                   allow_extended_gaps and 'true' or 'false',
                                   extension_percent,
                                   null_only and 'true' or 'false')
                    execute_query(query)
        except Exception, e:
            raise e
    
    @classmethod
    def set_density(cls, 
                    allow_extended_gaps=True, 
                    extension_percent='.2', 
                    null_only=True):
        
        try:
            set_chromosome_lists(cls)
            multiprocess_all_chromosomes(wrap_set_density, 
                                         cls, 
                                         allow_extended_gaps, 
                                         extension_percent, 
                                         null_only)
        except Exception, e:
            raise e
    
    @classmethod
    def _set_density(cls, chr_list, 
                     allow_extended_gaps=True, 
                     extension_percent='.2', 
                     null_only=True):
        '''
        Force reset average tags for prep DB.
        '''
        try: 
            for chr_id  in chr_list:
                print 'Setting density for transcripts for chr_id %d' % chr_id
                query = """
                    SELECT atlas_{}_{}_prep.set_density({},{},{},{},{},{},{});
                    """.format(current_settings.GENOME, 
                               current_settings.CELL_TYPE.lower(),
                               chr_id, current_settings.MAX_EDGE, 
                               EDGE_SCALING_FACTOR, 
                               current_settings.DENSITY_MULTIPLIER, 
                               allow_extended_gaps and 'true' or 'false',
                               extension_percent,
                               null_only and 'true' or 'false')
                execute_query(query)
        except Exception, e:
            raise e
            
    @classmethod
    def draw_transcript_edges(cls):
        try:
            set_chromosome_lists(cls)
            multiprocess_all_chromosomes(wrap_draw_transcript_edges, cls)
        except Exception, e:
            raise e
    @classmethod
    def _draw_transcript_edges(cls, chr_list):
        try:
            for chr_id in chr_list:
                print 'Drawing edges for transcripts for chr_id %d' % chr_id
                query = """
                    SELECT atlas_{0}_{1}{2}.draw_transcript_edges({chr_id},{3},{4});
                    """.format(current_settings.GENOME,
                           current_settings.CELL_TYPE.lower(),
                           current_settings.STAGING, 
                           MIN_ONE_RUN_TAGS, current_settings.MAX_EDGE,
                           chr_id=chr_id)
                execute_query(query)
        except Exception, e:
            raise e           
    
    @classmethod
    @commit_manually('default')
    def set_scores(cls):
        try:
            set_chromosome_lists(cls)
            active_cursor = get_cursor()
            print active_cursor
            multiprocess_all_chromosomes(wrap_set_scores, cls, active_cursor)
            commit_transaction()
        except Exception, e:
            rollback_transaction()
            raise e
        
    @classmethod
    def _set_scores(cls, chr_list, active_cursor=None):
        try:
            for chr_id in chr_list:
                print 'Scoring transcripts for chromosome %d' % chr_id
                query = """
                    SELECT atlas_{0}_{1}{2}.calculate_scores({chr_id});
                    SELECT atlas_{0}_{1}{2}.calculate_standard_error({chr_id});
                    """.format(current_settings.GENOME,
                           current_settings.CELL_TYPE.lower(),
                           current_settings.STAGING, chr_id=chr_id)
                execute_query_in_transaction(query, active_cursor=active_cursor)
        except Exception, e:
            rollback_transaction()
            raise e  
    
        
class FilteredAtlasTranscriptManager(models.Manager):
    def get_query_set(self):
        qset = super(FilteredAtlasTranscriptManager, self).get_query_set()
        return qset.filter(score__gte=MIN_SCORE)
    
class FilteredAtlasTranscript(object):
    '''
    Acts as a grouping of shared methods for filtered atlas transcripts.
    Not a model because the proxy models that will inherit these methods
    complain if they inherit from an abstract method.
    '''
    objects = FilteredAtlasTranscriptManager()
    
    ################################################
    # Visualization
    ################################################
    @classmethod
    def generate_bed_file(cls, output_dir):
        '''
        Generates a BED file (http://genome.ucsc.edu/FAQ/FAQformat.html#format1)
        of all the transcripts for viewing in the UCSC Genome Browser.
        '''
        max_score = cls.objects.aggregate(max=Max('score'))['max']
        transcripts = cls.objects.order_by('chromosome__id',
                                           'transcription_start')
        
        cls._generate_bed_file(output_dir, transcripts, max_score, strand=0)
        cls._generate_bed_file(output_dir,transcripts, max_score, strand=1)
        
    @classmethod
    def _generate_bed_file(cls, output_dir, transcripts, max_score, strand=0):
        file_name = 'Atlas_Transcripts_{}_{}.bed'.format(
                                            datetime.now().strftime('%Y_%m_%d'), 
                                            strand)
        file_path = os.path.join(output_dir, file_name)
        
        transcripts = transcripts.filter(strand=strand)
        
        strand_char = strand and '-' or '+'
        output = ('track name=vespucci_atlas_transcripts_{}_{}_{strand} ' \
                    + 'description="Vespucci Atlas Transcripts {strand_char} ' \
                    + 'strand" useScore=1 itemRgb=On\n'\
                    ).format(current_settings.GENOME, 
                             current_settings.CELL_TYPE,
                             strand=strand, 
                             strand_char=strand_char)
        
        for trans in transcripts:
            # chrom start end name score strand thick_start thick_end colors?
            # Make sure we don't go beyond the length of the chromosome.
            # Transcripts shouldn't due to previous processing, 
            # but just in case, we check here as well.
            start = max(0,trans.transcription_start)
            end = min(trans.chromosome.length,trans.transcription_end)
            row = [trans.chromosome.name, 
                   str(start), 
                   str(end), 
                   'Transcript_' + str(trans.id), 
                   str((float(trans.score)/max_score)*1000),
                   trans.strand and '-' or '+', 
                   str(start), 
                   str(end), 
                   trans.strand and '0,255,0' or '0,0,255']
            
            output += '\t'.join(row) + '\n'
        
        f = open(file_path, 'w')
        f.write(output)
        f.close()
        
class TranscriptSourceBase(TranscriptModelBase):
    sequencing_run          = models.ForeignKey(SequencingRun)
    tag_count               = models.IntegerField(max_length=12)
    gaps                    = models.IntegerField(max_length=12)
    
    class Meta(object):
        abstract = True
        
    def __unicode__(self):
        return '%s: %d tags from %s' % (self.__class__.__name__,
                                      self.tag_count,
                                      self.sequencing_run.source_table.strip())
        
class AtlasTranscriptSourcePrep(TranscriptSourceBase):
    class Meta(object):
        abstract = True

class AtlasTranscriptSource(TranscriptSourceBase):
    class Meta(object):
        abstract = True
        
class AtlasTranscriptTranscriptionRegionTable(TranscriptModelBase):
    REL_CHOICES = ('contains','is contained by','overlaps with','is equal to')
    relationship = models.CharField(max_length=100, choices=[(x,x) 
                                                    for x in REL_CHOICES])
    
    table_type = None
    related_class = None    
    
    class Meta(object): 
        abstract = True        
    
    def __unicode__(self):
        return 'AtlasTranscript %d %s %s' % (self.atlas_transcript.id, 
                                             self.relationship.strip(), 
                                             str(self.foreign_key_field()))    
    
    def foreign_key_field(self): 
        return getattr(self, '%s_transcription_region' % self.table_type)
        
class AtlasTranscriptSequence(AtlasTranscriptTranscriptionRegionTable):
    '''
    Relationship between AtlasTranscript and the sequence record it maps to.
    '''
    sequence_transcription_region = models.ForeignKey(SequenceTranscriptionRegion)
    
    table_type = 'sequence'
    related_class = SequenceTranscriptionRegion
    
    class Meta(object): 
        abstract = True
           
class AtlasTranscriptNonCoding(AtlasTranscriptTranscriptionRegionTable):
    '''
    Relationship between AtlasTranscript and the non coding region it maps to.
    '''
    non_coding_transcription_region = models.ForeignKey(NonCodingTranscriptionRegion)
    
    table_type = 'non_coding'
    related_class = NonCodingTranscriptionRegion

    class Meta(object): 
        abstract = True
            