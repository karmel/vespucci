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
from glasslab.glassatlas.datatypes.transcript import MAX_STITCHING_GAP

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
                                    start_end=(start, end)
                                    )
        # Add transcripts for tags
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        connection.close()
        
    def _assert_results_add_transcripts(self):
        total_tags = 0
        for run in self.sequencing_runs:
            GlassTag._meta.db_table = run.source_table.strip()
            
            # Get transcripts from this source
            transcripts = self.cell_base.glass_transcript.objects.filter(
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
                                    AND tag.start_end OPERATOR(public.<@) transcript.start_end
                                WHERE transcript.chromosome_id IS NULL''' %
                                (GlassTag._meta.db_table, 
                                 self.cell_base.glass_transcript._meta.db_table))
            self.assertEquals(not_contained[0][0],0)
            
        # Total count should equal transcript count, since no stitching has occured
        self.assertEquals(total_tags, 
                          self.cell_base.glass_transcript.objects.aggregate(
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
                                start_end=(1000, 1500)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=10001000, end=10001500,
                                start_end=(10001000, 10001500)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 2)
    
    def test_different_chromosomes(self):
        # Two transcripts from different chromosomes don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 1500)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=12,
                                start=1000, end=1500,
                                start_end=(1000, 1500)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 2)
    
    def test_different_strands(self):
        # Two transcripts from different strands don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 1500)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=1,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 1500)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 2)
    
    def test_overlapping(self):
        # Two transcripts that overlap stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 1500)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1200, end=1750,
                                start_end=(1200, 1750)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, 1000)
        self.assertEquals(trans.transcription_end, 1750)
        self.assertEquals(trans.strand, 0)
        self.assertEquals(trans.chromosome_id, 1)
        self.assertEquals(trans.start_end, '(1000),(1750)')
    
    def test_within_max_gap(self):
        # Two transcripts that are separated by less than max_gap stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 1000, 1500
        GlassTag.objects.create(strand=1,
                                chromosome_id=20,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = end + MAX_STITCHING_GAP, end + MAX_STITCHING_GAP + 1000
        GlassTag.objects.create(strand=1,
                                chromosome_id=20,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end_2)
        self.assertEquals(trans.strand, 1)
        self.assertEquals(trans.chromosome_id, 20)
        self.assertEquals(trans.start_end, '(%d),(%d)' % (start, end_2))
    
    def test_beyond_max_gap(self):
        # Two transcripts that are separated by more than max_gap don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 1004, 1504
        GlassTag.objects.create(strand=1,
                                chromosome_id=2,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = end + MAX_STITCHING_GAP + 1, end + MAX_STITCHING_GAP + 105
        GlassTag.objects.create(strand=1,
                                chromosome_id=2,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 2)
    
    def test_within_sequence(self):
        # Two transcripts that are contained within TNF stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 35336500, 35336550
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 35336800, 35336850
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end_2)
        self.assertEquals(trans.strand, 1)
        self.assertEquals(trans.chromosome_id, 17)
        self.assertEquals(trans.start_end, '(%d),(%d)' % (start, end_2))
    
    def test_large_gap_within_sequence(self):
        # Two transcripts that are contained within TNF but very far apart don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 35336500, 35336550
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 35337250, 35337300
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 2)
        
    def test_beyond_sequence(self):
        # Two transcripts that are close but not both within TNF don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 35336340, 35336400
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 35336270, 35336300
        GlassTag.objects.create(strand=1,
                                chromosome_id=17,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 2)
    
    ##################################################
    # Associating transcripts
    ##################################################
    def test_contains_sequence(self):
        # Transcript gets associated with Serbp1.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 67216950, 67225957
        GlassTag.objects.create(strand=0,
                                chromosome_id=6,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 67226000, 67239300
        GlassTag.objects.create(strand=0,
                                chromosome_id=6,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        # Four versions of Serbp1
        seqs = self.cell_base.glass_transcript_sequence.objects.all()
        self.assertEquals(seqs.count(), 4)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]

        self.assertEquals(seqs[0].relationship, 'contains')
        self.assertEquals(seqs[0].glass_transcript, trans)
        self.assertTrue(seqs.get(sequence_transcription_region__sequence_identifier__sequence_identifier='NM_025814'))
    
    def test_overlaps_with_sequence(self):
        # Transcript gets associated with Serbp1.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 67216950, 67225957
        GlassTag.objects.create(strand=0,
                                chromosome_id=6,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 67226000, 67238000
        GlassTag.objects.create(strand=0,
                                chromosome_id=6,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        # Four versions of Serbp1
        seqs = self.cell_base.glass_transcript_sequence.objects.all()
        self.assertEquals(seqs.count(), 4)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]

        self.assertEquals(seqs[0].relationship, 'overlaps with')
        self.assertEquals(seqs[0].glass_transcript, trans)
        self.assertTrue(seqs.get(sequence_transcription_region__sequence_identifier__sequence_identifier='NM_025814'))
        
    def test_is_contained_by_sequence(self):
        # Transcript gets associated with Serbp1.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 67218000, 67225957
        GlassTag.objects.create(strand=0,
                                chromosome_id=6,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 67226000, 67231000
        GlassTag.objects.create(strand=0,
                                chromosome_id=6,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        # Four versions of Serbp1
        seqs = self.cell_base.glass_transcript_sequence.objects.all()
        self.assertEquals(seqs.count(), 4)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]

        self.assertEquals(seqs[0].relationship, 'is contained by')
        self.assertEquals(seqs[0].glass_transcript, trans)
        self.assertTrue(seqs.get(sequence_transcription_region__sequence_identifier__sequence_identifier='NM_025814'))
     
    def test_is_equal_to_sequence(self):
        # Transcript gets associated with Serbp1.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 67216972, 67225957
        GlassTag.objects.create(strand=0,
                                chromosome_id=6,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 67226000, 67239296
        GlassTag.objects.create(strand=0,
                                chromosome_id=6,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        # Four versions of Serbp1
        seqs = self.cell_base.glass_transcript_sequence.objects.all()
        self.assertEquals(seqs.count(), 4)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]

        self.assertEquals(seqs[0].relationship, 'is equal to')
        self.assertEquals(seqs[0].glass_transcript, trans)
        self.assertTrue(seqs.get(sequence_transcription_region__sequence_identifier__sequence_identifier='NM_025814'))
    
    def test_contains_ncrna(self):
        # Transcript gets associated with ncRNA FR001521: non-protein coding (noncoding) transcript.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 13047530, 13047730
        GlassTag.objects.create(strand=1,
                                chromosome_id=15,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 13047740, 13050300
        GlassTag.objects.create(strand=1,
                                chromosome_id=15,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        
        ncrna = self.cell_base.glass_transcript_non_coding.objects.all()
        self.assertEquals(ncrna.count(), 1)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]

        self.assertEquals(ncrna[0].relationship, 'contains')
        self.assertEquals(ncrna[0].glass_transcript, trans)
        self.assertTrue(ncrna.get(non_coding_transcription_region__non_coding_rna__description__contains='FR001521'))
    
    def test_not_strand_matched(self):
        # Transcript does not get associated with mmu-mir-155.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 84714385, 84714400
        GlassTag.objects.create(strand=1,
                                chromosome_id=16,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 84714400, 84714449
        GlassTag.objects.create(strand=1,
                                chromosome_id=16,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        # Four versions of Serbp1
        seqs = self.cell_base.glass_transcript_sequence.objects.all()
        self.assertEquals(seqs.count(), 0)
        ncrna = self.cell_base.glass_transcript_non_coding.objects.all()
        self.assertEquals(ncrna.count(), 0)
        
    def test_contains_conserved(self):
        # Transcript gets associated with conserved regions.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 133183579, 133183800
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 133183600, 133185176
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        
        cons = self.cell_base.glass_transcript_conserved.objects.all()
        self.assertEquals(cons.count(), 8)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]

        self.assertEquals(cons[0].relationship, 'contains')
        self.assertEquals(cons[0].glass_transcript, trans)
    
    def test_is_contained_by_patterned(self):
        # Transcript gets associated simple repeat.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 122008915, 122009000
        GlassTag.objects.create(strand=0,
                                chromosome_id=9,
                                start=start, end=end,
                                start_end=(start, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 122009005, 122009100
        GlassTag.objects.create(strand=0,
                                chromosome_id=9,
                                start=start_2, end=end_2,
                                start_end=(start_2, end_2)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        
        patt = self.cell_base.glass_transcript_patterned.objects.all()
        self.assertEquals(patt.count(), 1)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]

        self.assertEquals(patt[0].relationship, 'is contained by')
        self.assertEquals(patt[0].glass_transcript, trans)
        self.assertTrue(patt.get(patterned_transcription_region__type='simple repeat'))

            
    ##################################################
    # Calculating scores
    ##################################################
    def test_score_short_transcript(self): 
        # Transcript of length < 1500 should have score = total tag count.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 1000, 1500
        for _ in xrange(0,10):
            GlassTag.objects.create(strand=1,
                                    chromosome_id=22,
                                    start=start + randint(-5,5), end=end + randint(-5,5),
                                    start_end=(start, end)
                                    )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 1010, 1510
        for _ in xrange(0,20):
            GlassTag.objects.create(strand=1,
                                    chromosome_id=22,
                                    start=start_2 + randint(-5,5), end=end_2 + randint(-5,5),
                                    start_end=(start_2, end_2)
                                    )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        self.cell_base.glass_transcript.set_scores()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(trans.score, 20)
        
    def test_score_1500_transcript(self): 
        # Transcript of length = 1500 should have score = total tag count.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 1000, 2500
        for _ in xrange(0,25):
            GlassTag.objects.create(strand=1,
                                    chromosome_id=22,
                                    start=start, end=end,
                                    start_end=(start, end)
                                    )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 1000, 2500
        for _ in xrange(0,20):
            GlassTag.objects.create(strand=1,
                                    chromosome_id=22,
                                    start=start_2, end=end_2,
                                    start_end=(start_2, end_2)
                                    )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        self.cell_base.glass_transcript.set_scores()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(trans.score, 25)
        
    def test_score_long_transcript(self): 
        # Transcript of length > 1500 should have score = total tag count/(lenght/1.5).
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='Gro-Seq')
        start, end = 100003, 103003
        for _ in xrange(0,20):
            GlassTag.objects.create(strand=1,
                                    chromosome_id=22,
                                    start=start, end=end,
                                    start_end=(start, end)
                                    )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='Gro-Seq')
        start_2, end_2 = 100003, 103003
        for _ in xrange(0,30):
            GlassTag.objects.create(strand=1,
                                    chromosome_id=22,
                                    start=start_2, end=end_2,
                                    start_end=(start_2, end_2)
                                    )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        self.cell_base.glass_transcript.set_scores()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcript.objects.count(), 1)
        
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(trans.score, 15)
    
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
                                start_end=(start, end)
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
                                start_end=(start + 100, end)
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
                                start_end=(start, end)
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
                                start_end=(start + 100, end)
                                )
        self.cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcript.stitch_together_transcripts()
        connection.close()
        
        trans = self.cell_base.glass_transcript.objects.all()
        
        new_seq = self.cell_base.glass_transcript_sequence.objects.order_by('id')[:1][0]

        self.assertEquals(trans.count(), 1)
        self.assertTrue(trans[0].requires_reload)
        self.assertNotEqual(curr_seq.id, new_seq.id)

if __name__=='__main__':
    unittest.main()