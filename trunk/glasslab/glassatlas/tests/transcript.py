'''
Created on Jan 4, 2011

@author: karmel
'''
import unittest
from glasslab.glassatlas.tests.base import GlassTestCase
from django.db import connection
from random import randint
from glasslab.sequencing.datatypes.tag import GlassTag
from django.db.models.aggregates import Sum
from glasslab.utils.database import fetch_rows
from glasslab.glassatlas.datatypes.transcript import MAX_STITCHING_GAP,\
    TAG_EXTENSION

class TranscriptTestCase(GlassTestCase):
    ##################################################
    # Adding transcripts directly from tags
    ##################################################   
    def test_add_transcripts_one_source(self):
        # Do all tags make it into the transcript table?
        self._add_transcripts_one_source(sequencing_run_name='sample_run_1')
        self._assert_results_add_transcripts()
    
    def test_add_transcripts_multi_source(self):
        # Do all tags make it into the transcript table?
        self._add_transcripts_one_source(sequencing_run_name='sample_run_1')
        self._add_transcripts_one_source(sequencing_run_name='sample_run_2')
        self._add_transcripts_one_source(sequencing_run_name='sample_run_3')
        self._assert_results_add_transcripts()
    
    def _add_transcripts_one_source(self, sequencing_run_name=''):
        self.create_tag_table(sequencing_run_name=sequencing_run_name, sequencing_run_type='Gro-Seq')
        
        # Add a random number of tags
        tag_count = randint(100, 999)
        for _ in xrange(0, tag_count):
            start = randint(0,1000000)
            end = start + randint(0,100000)
            GlassTag.objects.create(strand=randint(0,1),
                                    chromosome_id=randint(1,22),
                                    start=start, end=end,
                                    start_end=(start, 0, end, 0)
                                    )
        # Add transcripts for tags
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        connection.close()
        
    def _assert_results_add_transcripts(self):
        total_tags = 0
        for run in self.sequencing_runs:
            GlassTag._meta.db_table = run.source_table.strip()
            
            # Get transcripts from this source
            transcripts = self.cell_base.glass_transcript_prep.objects.filter(
                                                            glasstranscriptsource__sequencing_run=run)
            
            # Total count
            tag_count = GlassTag.objects.count()
            total_tags += tag_count
            self.assertEquals(tag_count, 
                              transcripts.aggregate(tags=Sum('glasstranscriptsource__tag_count'))['tags'])
            
            # Per strand count
            for strand in (0,1):
                self.assertEquals(GlassTag.objects.filter(strand=strand).count(), 
                                  transcripts.filter(strand=strand).aggregate(
                                            tags=Sum('glasstranscriptsource__tag_count'))['tags'])
            # Per chromosome count
            for chr_id in xrange(1,23):
                self.assertEquals(GlassTag.objects.filter(chromosome__id=chr_id).count(), 
                                  transcripts.filter(chromosome__id=chr_id).aggregate(
                                            tags=Sum('glasstranscriptsource__tag_count'))['tags'])
                
            # Ensure all tags are contained by transcripts
            not_contained = fetch_rows('''SELECT COUNT(tag.id) FROM "%s" tag
                                LEFT OUTER JOIN "%s" transcript
                                ON tag.chromosome_id = transcript.chromosome_id
                                    AND tag.strand = transcript.strand
                                    AND tag.start_end <@ transcript.start_end
                                WHERE transcript.chromosome_id IS NULL''' %
                                (GlassTag._meta.db_table, 
                                 self.cell_base.glass_transcript_prep._meta.db_table))
            self.assertEquals(not_contained[0][0],0)
            
        # Total count should equal transcript count, since no stitching has occured
        self.assertEquals(total_tags, 
                          self.cell_base.glass_transcript_prep.objects.aggregate(
                                        tags=Sum('glasstranscriptsource__tag_count'))['tags'])
    
    ##################################################
    # Stitching transcripts together
    ##################################################
    def test_disparate_regions(self):
        # Two transcripts from disparate regions don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=10001000, end=10001500,
                                start_end=(10001000, 0, 10001500, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 2)
    
    def test_different_chromosomes(self):
        # Two transcripts from different chromosomes don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=12,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 2)
    
    def test_different_strands(self):
        # Two transcripts from different strands don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=1,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 2)
    
    def test_overlapping(self):
        # Two transcripts that overlap stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1200, end=1750,
                                start_end=(1200, 0, 1750, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript_prep.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, 1000)
        self.assertEquals(trans.transcription_end, 1750)
        self.assertEquals(trans.strand, 0)
        self.assertEquals(trans.chromosome_id, 1)
        self.assertEquals(trans.start_end, '((1000,0), (1750,0))')
    
    def test_within_max_gap(self):
        # Two transcripts that are separated by less than max_gap stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 1000, 1500
        GlassTag.objects.create(strand=1,
                                chromosome_id=20,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = end + MAX_STITCHING_GAP, end + MAX_STITCHING_GAP + 1000
        GlassTag.objects.create(strand=1,
                                chromosome_id=20,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript_prep.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end_2)
        self.assertEquals(trans.strand, 1)
        self.assertEquals(trans.chromosome_id, 20)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, end_2))
    
    def test_beyond_max_gap(self):
        # Two transcripts that are separated by more than max_gap don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 10040, 15040
        GlassTag.objects.create(strand=1,
                                chromosome_id=2,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2= end + MAX_STITCHING_GAP + TAG_EXTENSION + 1
        end_2 = start_2 + 105
        GlassTag.objects.create(strand=1,
                                chromosome_id=2,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 2)
    
    def test_within_sequence(self):
        # Two transcripts that are contained within TNF stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 35336500, 35336550
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 35336800, 35336850
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript_prep.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end_2)
        self.assertEquals(trans.strand, 1)
        self.assertEquals(trans.chromosome_id, 17)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, end_2))
    
    def test_large_gap_within_sequence(self):
        # Two transcripts that are contained within TNF but very far apart don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 35336500, 35336550
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 35337250, 35337300
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 2)
        
    def test_beyond_sequence(self):
        # Two transcripts that are close but not both within TNF don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 35336340, 35336400
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 35336240, 35336270
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript_prep.objects.count(), 2)
    
    
    '''
    @deprecated: 
    ##################################################
    # Requiring rerun
    ##################################################
    def test_stitched_no_reload(self): 
        # If the transcript is stitched without change, no reload should occur
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        chr_id, start, end = 6, 67218000, 67225957
        GlassTag.objects.create(strand=0,
                                chromosome_id=chr_id,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        self.cell_base.glass_transcript.stitch_together_transcripts()
        
        connection.close()
        self.cell_base.glass_transcript.mark_all_reloaded()
        # Get seq assoc
        curr_seq = self.cell_base.glass_transcript_sequence.objects.order_by('id')[:1][0]
        connection.close()
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=chr_id,
                                start=start + 100, end=end,
                                start_end=(start + 100, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        
        trans = self.cell_base.glass_transcript.objects.all()
        
        new_seq = self.cell_base.glass_transcript_sequence.objects.order_by('id')[:1][0]

        self.assertEquals(trans.count(), 1)
        self.assertFalse(trans[0].requires_reload)
        self.assertEquals(curr_seq.id, new_seq.id)
    
    def test_stitched_requires_reload(self): 
        # If the transcript is stitched without change, no reload should occur
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        chr_id, start, end = 6, 67218000, 67225957
        GlassTag.objects.create(strand=0,
                                chromosome_id=chr_id,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.cell_base.glass_transcript.mark_all_reloaded()
        
        # Get seq assoc
        curr_seq = self.cell_base.glass_transcript_sequence.objects.order_by('id')[:1][0]
        connection.close()
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=chr_id,
                                start=start - 100, end=end,
                                start_end=(start + 100, 0, end, 0)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        
        trans = self.cell_base.glass_transcript.objects.all()
        
        new_seq = self.cell_base.glass_transcript_sequence.objects.order_by('id')[:1][0]

        self.assertEquals(trans.count(), 1)
        self.assertTrue(trans[0].requires_reload)
        self.assertNotEqual(curr_seq.id, new_seq.id)
'''

if __name__=='__main__':
    unittest.main()