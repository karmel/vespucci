'''
Created on Jan 5, 2011

@author: karmel
'''
from glasslab.glassatlas.tests.base import GlassTestCase
from random import randint
from glasslab.sequencing.datatypes.tag import GlassTag
from django.db import connection
from django.db.models.aggregates import Sum
from glasslab.utils.database import fetch_rows
from glasslab.glassatlas.datatypes.transcribed_rna import MAX_GAP_RNA


class TranscribedRnaTestCase(GlassTestCase):
  
    ##################################################
    # Adding transcribed RNA
    ##################################################
     
    def test_add_transcribed_rna_one_source(self):
        # Do all tags make it into the transcript table?
        self._add_transcribed_rna_one_source(sequencing_run_name='sample_run_1')
        self._assert_results_add_transcribed_rna()
    
    def test_add_transcribed_rna_multi_source(self):
        # Do all tags make it into the transcript table?
        self._add_transcribed_rna_one_source(sequencing_run_name='sample_run_1')
        self._add_transcribed_rna_one_source(sequencing_run_name='sample_run_2')
        self._add_transcribed_rna_one_source(sequencing_run_name='sample_run_3')
        self._assert_results_add_transcribed_rna()
    
    def _add_transcribed_rna_one_source(self, sequencing_run_name=''):
        self.create_tag_table(sequencing_run_name=sequencing_run_name, sequencing_run_type='RNA-Seq')
        
        # Add a random number of tags
        tag_count = randint(100, 999)
        for _ in xrange(0, tag_count):
            start = randint(0,1000000)
            end = start + randint(0,100000)
            GlassTag.objects.create(strand=randint(0,1),
                                    chromosome_id=randint(1,22),
                                    start=start, end=end,
                                    start_end=(start,0, end, 0)
                                    )
        # Add transcribed_rna for tags
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        connection.close()
        
    def _assert_results_add_transcribed_rna(self):
        total_tags = 0
        for run in self.sequencing_runs:
            GlassTag._meta.db_table = run.source_table.strip()
            
            # Get transcribed_rna from this source
            transcribed_rna = self.cell_base.glass_transcribed_rna.objects.filter(
                                                            glasstranscribedrnasource__sequencing_run=run)
            
            # Total count
            tag_count = GlassTag.objects.count()
            total_tags += tag_count
            self.assertEquals(tag_count, 
                              transcribed_rna.aggregate(tags=Sum('glasstranscribedrnasource__tag_count'))['tags'])
            
            # Per strand count
            for strand in (0,1):
                self.assertEquals(GlassTag.objects.filter(strand=strand).count(), 
                                  transcribed_rna.filter(strand=strand).aggregate(
                                            tags=Sum('glasstranscribedrnasource__tag_count'))['tags'])
            # Per chromosome count
            for chr_id in xrange(1,23):
                self.assertEquals(GlassTag.objects.filter(chromosome__id=chr_id).count(), 
                                  transcribed_rna.filter(chromosome__id=chr_id).aggregate(
                                            tags=Sum('glasstranscribedrnasource__tag_count'))['tags'])
                
            # Ensure all tags are contained by transcribed_rna
            not_contained = fetch_rows('''SELECT COUNT(tag.id) FROM "%s" tag
                                LEFT OUTER JOIN "%s" trans_rna
                                ON tag.chromosome_id = trans_rna.chromosome_id
                                    AND tag.strand = trans_rna.strand
                                    AND tag.start_end <@ trans_rna.start_end
                                WHERE trans_rna.chromosome_id IS NULL''' %
                                (GlassTag._meta.db_table, 
                                 self.cell_base.glass_transcribed_rna._meta.db_table))
            self.assertEquals(not_contained[0][0],0)
            
        # Total count should equal transcript count, since no stitching has occured
        self.assertEquals(total_tags, 
                          self.cell_base.glass_transcribed_rna.objects.aggregate(
                                        tags=Sum('glasstranscribedrnasource__tag_count'))['tags'])
    
    ##################################################
    # Stitching transcribed RNAs together
    ##################################################
    
    def test_disparate_regions(self):
        # Two transcribed RNAs from disparate regions don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=10001000, end=10001500,
                                start_end=(10001000,0, 10001500, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 2)
    
    def test_different_chromosomes(self):
        # Two transcribed RNAs from different chromosomes don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=12,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 2)
    
    def test_different_strands(self):
        # Two transcribed RNAs from different strands don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        GlassTag.objects.create(strand=1,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 2)
    
    def test_overlapping(self):
        # Two transcribed RNAs that overlap stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1000, end=1500,
                                start_end=(1000, 0, 1500, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        GlassTag.objects.create(strand=0,
                                chromosome_id=1,
                                start=1200, end=1750,
                                start_end=(1200, 0, 1750, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 1)
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, 1000)
        self.assertEquals(trans.transcription_end, 1750)
        self.assertEquals(trans.strand, 0)
        self.assertEquals(trans.chromosome_id, 1)
        self.assertEquals(trans.start_end, '((1000, 0), (1750, 0))')
    
    def test_within_max_gap(self):
        # Two transcribed RNAs that are separated by less than max_gap stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 1000, 1500
        GlassTag.objects.create(strand=1,
                                chromosome_id=20,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = end + MAX_GAP_RNA, end + MAX_GAP_RNA + 1000
        GlassTag.objects.create(strand=1,
                                chromosome_id=20,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 1)
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end_2)
        self.assertEquals(trans.strand, 1)
        self.assertEquals(trans.chromosome_id, 20)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, end_2))
    
    def test_beyond_max_gap(self):
        # Two transcribed RNAs that are separated by more than max_gap don't stitch.
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 1004, 1504
        GlassTag.objects.create(strand=1,
                                chromosome_id=2,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = end + MAX_GAP_RNA + 1, end + MAX_GAP_RNA + 105
        GlassTag.objects.create(strand=1,
                                chromosome_id=2,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 2)

    def test_within_ncrna(self):
        # Two transcribed RNAs that are contained within Slc25a10 exon stitch.
        chr, strand = 14, 0
        self._create_transcript(chr, strand, 64503150, 64506335)
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 64503155, 64503180
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = 64503200, 64503255
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 1)
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end_2)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, end_2))

    def test_different_ncrna_overlapping(self):
        # Two transcribed RNAs that do not share ncRNA should join if they overlap
        chr, strand = 14, 0
        #self._create_transcript(chr, strand, 64503150, 64506335)
        self._create_transcript(chr, strand, 64503150, 64507000)
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 64503155, 64506335
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = 64506335, 64507000
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 1)
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end_2)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, end_2))
    
    def test_different_ncrna_not_overlapping(self):
        # Two transcribed RNAs that do not share ncRNA should not join if they do not overlap
        chr, strand = 14, 0
        #self._create_transcript(chr, strand, 64503150, 64506335)
        self._create_transcript(chr, strand, 64503150, 64507000)
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 64503155, 64506335
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = 64506336, 64507000
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 2)
    
    def test_within_exon(self):
        # Two transcribed RNAs that are contained within Slc25a10 exon stitch.
        chr, strand = 11, 0
        self._create_transcript(chr, strand, 120350000, 120370000)
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 120359500, 120360000
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = 120360500, 120361000
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 1)
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end_2)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, end_2))
    
    def test_within_exon_different_transcripts(self):
        # Two transcribed RNAs that are contained within Slc25a10 exon stitch.
        chr, strand = 11, 0
        self._create_transcript(chr, strand, 120350000, 120360000)
        self._create_transcript(chr, strand, 120360500, 120370000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 120359500, 120360000
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = 120360500, 120361000
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 2)
    
    def test_large_gap_within_exon(self):
        # Two transcribed RNAs that are contained within Slc25a10 exon but very far apart don't stitch.
        chr, strand = 11, 0
        self._create_transcript(chr, strand, 120350000, 120370000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 120359500, 120360000
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = 120362000, 120362500
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 2)
    
    def test_beyond_exon(self):
        # Two transcribed RNAs that are close but not both within Slc25a10 exon don't stitch.
        chr, strand = 11, 0
        self._create_transcript(chr, strand, 120350000, 120370000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 120362480, 120362550
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.create_tag_table(sequencing_run_name='sample_run_2', sequencing_run_type='RNA-Seq')
        start_2, end_2 = 120360500, 120362470
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start_2, end=end_2,
                                start_end=(start_2, 0, end_2, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        self.assertEquals(self.cell_base.glass_transcribed_rna.objects.count(), 2)
    
    ##################################################
    # Associating transcribed RNA
    ##################################################
    def test_associate_different_strand(self):
        # Transcript doesn't match RNA strand; not associated.
        chr, strand = 3, 1
        source_1 = self._create_transcript(chr, 0, 1000, 5000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 1010, 1100
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        connection.close()
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, 0, end, 0))
        self.assertEquals(trans.glass_transcript, None)
        
    def test_associate_transcript_contains(self):
        # Transcript contains RNA; associated.
        chr, strand = 3, 1
        source_1 = self._create_transcript(chr, strand, 1000, 5000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 1010, 1100
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        connection.close()
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, 0, end, 0))
        self.assertEquals(trans.glass_transcript.glasstranscriptsource.all(
                            )[0].sequencing_run.name.strip().replace('tag_',''), 
                            source_1)
        
    def test_associate_transcript_overlaps(self):
        # Transcript overlaps RNA; associated.
        chr, strand = 3, 1
        source_1 = self._create_transcript(chr, strand, 1000, 5000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 900, 1100
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        connection.close()
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, 0, end, 0))
        self.assertEquals(trans.glass_transcript.glasstranscriptsource.all(
                            )[0].sequencing_run.name.strip().replace('tag_',''), 
                            source_1)

    def test_associate_largest(self):
        # Two transcripts contain RNA; larger one is assigned
        chr, strand = 3, 1
        source_2 = self._create_transcript(chr, strand, 1000, 2000)
        source_1 = self._create_transcript(chr, strand, 1000, 5000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 1010, 1100
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
            
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        connection.close()
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, 0, end, 0))
        self.assertEquals(trans.glass_transcript.glasstranscriptsource.all(
                            )[0].sequencing_run.name.strip().replace('tag_',''), 
                            source_1)
     
    def test_associate_minimal_overhang(self):
        # Two transcripts overlap with RNA; one with least overhand associates.
        chr, strand = 3, 1
        source_2 = self._create_transcript(chr, strand, 500, 1000)
        source_1 = self._create_transcript(chr, strand, 1000, 5000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 900, 1500
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        connection.close()
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, 0, end, 0))
        self.assertEquals(trans.glass_transcript.glasstranscriptsource.all(
                            )[0].sequencing_run.name.strip().replace('tag_',''), 
                            source_1)
    
    ##################################################
    # Marking as spliced transcripts
    ##################################################
    def test_associate_one(self):
        # One transcribed RNA is insufficient
        chr, strand = 3, 1
        source_2 = self._create_transcript(chr, strand, 500, 1000)
        source_1 = self._create_transcript(chr, strand, 1000, 5000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 900, 1500
        GlassTag.objects.create(strand=strand,
                                chromosome_id=chr,
                                start=start, end=end,
                                start_end=(start, 0, end, 0)
                                )
        self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        
        self.assertFalse(trans.glass_transcript.spliced)
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, 0, end, 0))
        self.assertEquals(trans.glass_transcript.glasstranscriptsource.all(
                            )[0].sequencing_run.name.strip().replace('tag_',''), 
                            source_1)
        
    def test_associate_two(self):
        # Two transcribed RNAs are sufficient
        chr, strand = 3, 1
        source_2 = self._create_transcript(chr, strand, 500, 1000)
        source_1 = self._create_transcript(chr, strand, 1000, 5000)
        
        self.create_tag_table(sequencing_run_name='sample_run_1', sequencing_run_type='RNA-Seq')
        start, end = 900, 1500
        for _ in xrange(0,2):
            GlassTag.objects.create(strand=strand,
                                    chromosome_id=chr,
                                    start=start, end=end,
                                    start_end=(start, 0, end, 0)
                                    )
            self.cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
            connection.close()
            
        self.cell_base.glass_transcribed_rna.associate_transcribed_rna()
        self.cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        connection.close()
        
        trans = self.cell_base.glass_transcribed_rna.objects.all()[:1][0]
        
        self.assertTrue(trans.glass_transcript.spliced)
        self.assertEquals(trans.transcription_start, start)
        self.assertEquals(trans.transcription_end, end)
        self.assertEquals(trans.strand, strand)
        self.assertEquals(trans.chromosome_id, chr)
        self.assertEquals(trans.start_end, '((%d, 0), (%d, 0))' % (start, 0, end, 0))
        self.assertEquals(trans.glass_transcript.glasstranscriptsource.all(
                            )[0].sequencing_run.name.strip().replace('tag_',''), 
                            source_1)
        