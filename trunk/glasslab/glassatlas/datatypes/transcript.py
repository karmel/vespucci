'''
Created on Nov 8, 2010

@author: karmel
'''
from __future__ import division
from glasslab.config import current_settings
from django.db import models, connection, transaction
from glasslab.utils.datatypes.genome_reference import Chromosome,\
    SequenceTranscriptionRegion, PatternedTranscriptionRegion,\
    ConservedTranscriptionRegion, NonCodingTranscriptionRegion
from glasslab.glassatlas.datatypes.metadata import SequencingRun
from glasslab.sequencing.datatypes.tag import multiprocess_glass_tags,\
    wrap_errors
from glasslab.utils.datatypes.basic_model import CubeField
from django.db.models.aggregates import Sum
from multiprocessing import Pool

MAX_SEQUENCE_GAP = 2000 # Max gap between transcripts that share sequence associations
MAX_OTHER_GAP = 200 # Max gap between transcripts that share no sequence associations

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
    
def wrap_add_transcripts_from_tags(cls, chr_list, *args): 
    wrap_errors(cls._add_transcripts_from_tags_for_chr_list, chr_list, *args)

def wrap_stitch_together_transcripts(cls, chr_list): 
    wrap_errors(cls._stitch_together_transcripts, chr_list)

class GlassTranscript(models.Model):
    '''
    Unique transcribed regions in the genome.
    '''   
    # Use JS for browser link to auto-include in Django Admin form 
    ucsc_browser_link = '''<a href="#" onclick="window.open('http://genome.ucsc.edu/cgi-bin/hgTracks?db='''\
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
        multiprocess_glass_tags(wrap_add_transcripts_from_tags, cls, sequencing_run)
        #wrap_add_transcripts_from_tags(cls,[21, 22],sequencing_run)

    @classmethod
    def _add_transcripts_from_tags_for_chr_list(cls, chr_list, sequencing_run):
        for chr_id in chr_list:
            print 'Adding transcripts for chromosome %d' % chr_id
            cls._add_transcripts_from_tags(chr_id, sequencing_run)
    
    @classmethod
    def _add_transcripts_from_tags(cls, chromosome_id, sequencing_run):
        query = """
            SELECT glass_atlas_%s.save_transcripts_from_sequencing_run(%d, %d,'%s', %d);
            """ % (current_settings.TRANSCRIPT_GENOME,
                   sequencing_run.id, chromosome_id, 
                   sequencing_run.source_table.strip(), MAX_OTHER_GAP)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(query)
        transaction.commit_unless_managed()
    
    def save_final_transcript(self):
        self.set_score()
        self.save()
        self.save_all_transcription_region_matches()      
        
    def set_score(self):
        '''
        Scoring, currently, is rudimentary::
         
            total tags recorded for this transcript across all sequencing runs
            x number of sequencing runs this transcript appears in
            / total number of sequencing runs possible
        
        '''
        total_tags = GlassTranscriptSource.objects.filter(glass_transcript=self
                                            ).aggregate(total_tags=Sum('tag_count'))['total_tags']
        relevant_runs = GlassTranscriptSource.objects.filter(glass_transcript=self
                                            ).values('sequencing_run_id').distinct().count()
        total_runs = GlassTranscriptSource.objects.values('sequencing_run_id').distinct().count()
       
        try: self.score = (total_tags*relevant_runs)/total_runs
        except Exception:
            print 'Erroneous score calculation: total tags = %s, relevant_runs = %s for transcript %s'\
                         % (str(total_tags), str(relevant_runs), str(self))
            raise
    
    def save_all_transcription_region_matches(self):
        for region_class in GlassTranscriptTranscriptionRegionTable.get_children():
            self.save_transcription_region_matches(region_class)
        
    def save_transcription_region_matches(self, region_class):
        '''
        Find all transcription regions that overlap this one.
        Save or update records accordingly.
        
        Not explicitly transaction wrappe din case it's part of a larger process.
        '''
        # First get existing records.
        existing = region_class.objects.filter(glass_transcript=self)
        
        current = region_class.related_class.objects.raw("""
                        SELECT reg.* FROM "%s" reg
                        JOIN "%s" transcript
                        ON reg.chromosome_id = transcript.chromosome_id 
                        AND reg.start_end OPERATOR(public.&&) transcript.start_end
                        WHERE transcript.id = %d;"""  % (
                                            region_class.related_class._meta.db_table,
                                            GlassTranscript._meta.db_table,
                                            self.id),)
        
        saved_ids = []
        for region in current:
            try:
                record = existing.get(**{'%s_transcription_region__id' % region_class.table_type: region.id})
            except region_class.DoesNotExist:
                record = region_class(**{'glass_transcript': self,
                                         '%s_transcription_region' % region_class.table_type: region})
            # Who contains who?
            if abs(self.transcription_start - region.transcription_start) <= 10 \
                and abs(self.transcription_end - region.transcription_end) <= 10:
                    record.relationship = 'is equal to'
            elif self.transcription_start <= region.transcription_start \
                and self.transcription_end >= region.transcription_end:
                    record.relationship = 'contains'
            elif self.transcription_start >= region.transcription_start \
                and self.transcription_end <= region.transcription_end:
                    record.relationship = 'is contained by'
            else: record.relationship = 'overlaps with'
            
            record.save()
            saved_ids.append(record.id)
        
        # Finally, delete excess records.
        existing.exclude(id__in=saved_ids).delete()
        
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
                """ % (current_settings.TRANSCRIPT_GENOME, 
                       chr_id, MAX_SEQUENCE_GAP, MAX_OTHER_GAP)
            connection.close()
            cursor = connection.cursor()
            cursor.execute(query)
            transaction.commit_unless_managed()
        
    @classmethod
    def _stitch_together_transcripts_x(cls, chr_list):
        '''
        Gapping causes us to get little transcripts where we should have one large one.
        
        Here we stitch smaller transcripts together if and only if
        they share the exact same set of sequence and non_coding region mappings
        and the gap between any two regions is less than 2kb.
        
        Next, we stitch together transcripts not matched to any sequences
        if the gap is less than 200bp, and the non-coding regions match.
        '''
        for chr_id in chr_list:
            print 'Stitching together transcripts for chromosome %d' % chr_id
            seq_groups = cls._get_transcript_groups(chr_id)
            for id_group, seq_group in seq_groups:
                if seq_group: max_gap = 2000
                else: max_gap = 200 # Allow a smaller gap for transcripts not associated with sequences.
                transcripts = cls.objects.filter(id__in=id_group).order_by('transcription_start','-transcription_end')
                cls._merge_transcript_group(transcripts, max_gap=max_gap)        
        
    @classmethod
    def _get_transcript_groups(cls, chr_id):
        # First, pull groups of transcript ids.
        query = """
        SELECT 
            array_agg(transcript.id),
            grouped_seq.regions
        FROM "%s" transcript
        LEFT OUTER JOIN (SELECT 
                glass_transcript_id, 
                public.sort(array_agg(sequence_transcription_region_id)::int[]) as regions
            FROM "%s"
            GROUP BY glass_transcript_id) grouped_seq
        ON transcript.id = grouped_seq.glass_transcript_id
        LEFT OUTER JOIN (SELECT 
                glass_transcript_id, 
                public.sort(array_agg(non_coding_transcription_region_id)::int[]) as regions
            FROM "%s"
            GROUP BY glass_transcript_id) grouped_nc
        ON transcript.id = grouped_nc.glass_transcript_id
        WHERE transcript.chromosome_id = %d
        GROUP BY grouped_seq.regions, grouped_nc.regions
        HAVING count(transcript.id) > 1;""" % (GlassTranscript._meta.db_table,
                                               GlassTranscriptSequence._meta.db_table,
                                               GlassTranscriptNonCoding._meta.db_table,
                                               chr_id)
        connection.close()
        cursor = connection.cursor()
        cursor.execute(query)
        
        rows = cursor.fetchall()
        
        # Returns rows of arrays: [([29695, 29700,],),([28574, 2875440,])]
        # Flatten into list of lists and return
        return rows
    
    @classmethod
    @transaction.commit_manually
    def _merge_transcript_group(cls, transcripts, max_gap=0):
        '''
        Transcripts all share sequence and non_coding region mappings,
        and are ordered by start ascending.
        
        Merge together as many as possible without any gaps > 2kb
        '''
        try:
            merged_trans = transcripts[0]
            merged = False
            for trans in transcripts[1:]:
                if merged_trans.transcription_end >= trans.transcription_start \
                    or trans.transcription_start - merged_trans.transcription_end <= max_gap:
                        merged_trans.transcription_end = max(merged_trans.transcription_end, trans.transcription_end)
                        if trans.strand_0: merged_trans.strand_0 = True
                        if trans.strand_1: merged_trans.strand_1 = True
                        if trans.spliced: merged_trans.spliced = True
                        merged_trans.start_end = (merged_trans.transcription_start, merged_trans.transcription_end)
                        trans.replace_records(merged_trans)
                        trans.delete()
                        merged = True
                else:
                    if merged:
                        # Close off current merged transcript
                        merged_trans.save_final_transcript()
                    
                    # And reset
                    merged_trans = trans
                    merged = False
            
            # Close off final merged_trans
            if merged: merged_trans.save_final_transcript()
            transaction.commit()
        
        except Exception:
            transaction.rollback()
            raise

    def replace_records(self, new_trans):
        '''
        Replace all associations of this transcript with the new transcript.
        ''' 
        self._replace_records_for_source(new_trans)
        for region_class in GlassTranscriptTranscriptionRegionTable.get_children():
            self._replace_records_for_region(new_trans, region_class)
        
    def _replace_records_for_source(self, new_trans):
        for rel in GlassTranscriptSource.objects.filter(glass_transcript=self):
            try:
                existing = GlassTranscriptSource.objects.get(glass_transcript = new_trans,
                                                            sequencing_run = rel.sequencing_run)
                existing.tag_count += rel.tag_count
                existing.gaps += rel.gaps
                existing.save()
                rel.delete()
            except GlassTranscriptSource.DoesNotExist:
                rel.glass_transcript = new_trans
                rel.save()
                
    def _replace_records_for_region(self, new_trans, region_class):
        for rel in region_class.objects.filter(glass_transcript=self):
            try:
                existing = region_class.objects.get(**{'glass_transcript': new_trans,
                                '%s_transcription_region' % region_class.table_type: rel.foreign_key_field()})
                rel.delete()
            except region_class.DoesNotExist:
                rel.glass_transcript = new_trans
                rel.save()
        
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
    