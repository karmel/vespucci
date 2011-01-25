'''
Created on Jan 18, 2011

@author: karmel

Are features added and removed correctly?
'''
from glasslab.glassatlas.tests.base import GlassTestCase
from glasslab.sequencing.datatypes.peak import GlassPeak
from django.db import connection
from glasslab.glassatlas.datatypes.metadata import SequencingRun

class FeatureTestCase(GlassTestCase):
    def create_peak_table(self, sequencing_run_name='', sequencing_run_type='ChIP-Seq'):
        '''
        Can be called in order to create tag tables (split by chromosome)
        for the passed run name.
        '''
        # Reset class vars that in normal circumstances do not get reset
        GlassPeak._chromosomes = None
        GlassPeak.create_table(sequencing_run_name)
        GlassPeak.add_indices()
        self.sequencing_runs.append(GlassPeak.add_record_of_tags(description='Created during a unit test.', 
                                                                type=sequencing_run_type))
        connection.close()
      
    def test_peak_type_determination_0(self):
        GlassPeak._peak_type = None
        peak_type = GlassPeak.peak_type('1234_H3k4ME1_hrgsf')
        self.assertEquals(peak_type.type.strip(), 'H3K4me1')

    def test_peak_type_determination_1(self):
        GlassPeak._peak_type = None
        peak_type = GlassPeak.peak_type('1234_H3k4Mq1_hrgsf')
        self.assertEquals(peak_type, None)
        
    def test_peak_type_determination_2(self):
        GlassPeak._peak_type = None
        peak_type = GlassPeak.peak_type('12h4k12acgsf')
        self.assertEquals(peak_type.type.strip(), 'H4K12ac')
    
    def test_transcript_equals(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 1, 1000, 1500
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        source_1 = self._create_transcript(chr_1, 0, start_1, end_1)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship.strip(), 'is equal to')
        self.assertEquals(instance.peak_feature, feature)
        self.assertEquals(instance.distance_to_tss, 250)
        
    def test_transcript_contains(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 3, 58345, 58945
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        source_1 = self._create_transcript(chr_1, 1, start_1-1, end_1)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship.strip(), 'contains')
        self.assertEquals(instance.peak_feature, feature)
        self.assertEquals(instance.distance_to_tss, 300)

    def test_transcript_is_contained_by(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 14, 100000900, 100010900
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        source_1 = self._create_transcript(chr_1, 0, start_1+1, end_1)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship.strip(), 'is contained by')
        self.assertEquals(instance.peak_feature, feature)
        self.assertEquals(instance.distance_to_tss, 4999)
    
    def test_transcript_overlaps_with(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 21, 9999, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        source_1 = self._create_transcript(chr_1, 1, start_1-100, end_1-101)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship.strip(), 'overlaps with')
        self.assertEquals(instance.peak_feature, feature)
        self.assertEquals(instance.distance_to_tss, 0)
    
    def test_transcript_is_upstream_of_0(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 12, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        source_1 = self._create_transcript(chr_1, 0, 7500, 9500)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship.strip(), 'is upstream of')
        self.assertEquals(instance.peak_feature, feature)
        self.assertEquals(instance.distance_to_tss, 2600)
    
    def test_transcript_is_upstream_of_1(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 12, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        source_1 = self._create_transcript(chr_1, 1, 10500, 11500)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship.strip(), 'is upstream of')
        self.assertEquals(instance.peak_feature, feature)
        self.assertEquals(instance.distance_to_tss, 1400)
    
    def test_transcript_is_downstream_of_0(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 15, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        source_1 = self._create_transcript(chr_1, 0, 10500, 11500)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship.strip(), 'is downstream of')
        self.assertEquals(instance.peak_feature, feature)
        self.assertEquals(instance.distance_to_tss, 400)
    
    def test_transcript_is_downstream_of_1(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 15, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        source_1 = self._create_transcript(chr_1, 1, 7500, 9500)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship.strip(), 'is downstream of')
        self.assertEquals(instance.peak_feature, feature)
        self.assertEquals(instance.distance_to_tss, 600)
        
    def test_transcript_two_peaks(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 15, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1+100, end=end_1+100,
                                start_end=(start_1+100, end_1+100)
                                )
        
        source_1 = self._create_transcript(chr_1, 0, start_1-300, start_1)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature_1 = self.cell_base.peak_feature.objects.get(relationship='overlaps with')
        feature_2 = self.cell_base.peak_feature.objects.get(relationship='is upstream of')
        instance_1 = self.cell_base.peak_feature_instance.objects.get(peak_feature=feature_1)
        instance_2 = self.cell_base.peak_feature_instance.objects.get(peak_feature=feature_2)
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature_1.glass_transcript, trans)
        self.assertEquals(feature_2.glass_transcript, trans)
        self.assertEquals(instance_1.distance_to_tss, 400)
        self.assertEquals(instance_2.distance_to_tss, 500)
        
    def test_transcript_no_peaks_0(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 15, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1+100, end=end_1+100,
                                start_end=(start_1+100, end_1+100)
                                )
        
        source_1 = self._create_transcript(1, 0, start_1-300, start_1)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        count = self.cell_base.peak_feature.objects.count()
        self.assertFalse(count)
    
    def test_transcript_no_peaks_1(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 15, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1+100, end=end_1+100,
                                start_end=(start_1+100, end_1+100)
                                )
        
        source_1 = self._create_transcript(chr_1, 0, 300, 4999)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        count = self.cell_base.peak_feature.objects.count()
        self.assertFalse(count)
        
    def test_transcript_one_peak(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 15, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1+100, end=end_1+100,
                                start_end=(start_1+100, end_1+100)
                                )
        
        source_1 = self._create_transcript(chr_1, 0, 300, 8000)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        count = self.cell_base.peak_feature.objects.count()
        self.assertTrue(count)
        
    def test_two_transcripts(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 5, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        source_1 = self._create_transcript(chr_1, 0, start_1-300, start_1)
        source_2 = self._create_transcript(chr_1, 0, end_1+1, end_1+500)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature_1 = self.cell_base.peak_feature.objects.get(glass_transcript__id=1)
        feature_2 = self.cell_base.peak_feature.objects.get(glass_transcript__id=2)
        instance_1 = self.cell_base.peak_feature_instance.objects.get(peak_feature=feature_1)
        instance_2 = self.cell_base.peak_feature_instance.objects.get(peak_feature=feature_2)
        self.assertEquals(feature_1.relationship, 'overlaps with')
        self.assertEquals(feature_2.relationship, 'is downstream of')
        self.assertEquals(instance_1.distance_to_tss, 400)
        self.assertEquals(instance_2.distance_to_tss, 101)
    
    def test_change_transcript(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 25, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        source_1 = self._create_transcript(chr_1, 0, start_1-300, start_1)
        connection.close()
        self.cell_base.peak_feature.add_from_peaks(GlassPeak._meta.db_table)
        connection.close()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship, 'overlaps with')
        self.assertEquals(instance.distance_to_tss, 400)
        
        trans.transcription_start = start_1 - 500
        trans.transcription_end = end_1 + 100
        trans.start_end = (trans.transcription_start, trans.transcription_end)
        trans.requires_reload = True
        trans.save()
        
        connection.close()
        self.cell_base.peak_feature.update_peak_features_by_transcript()
        connection.close()
        
        count = self.cell_base.peak_feature.objects.count()
        feature = self.cell_base.peak_feature.objects.all()[:1][0]
        instance = self.cell_base.peak_feature_instance.objects.all()[:1][0]
        trans = self.cell_base.glass_transcript.objects.all()[:1][0]
        self.assertEquals(count, 1)
        self.assertEquals(feature.glass_transcript, trans)
        self.assertEquals(feature.relationship, 'contains')
        self.assertEquals(instance.distance_to_tss, 600)
        
    def test_no_reload(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 5, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        source_1 = self._create_transcript(chr_1, 0, start_1-300, start_1)
        connection.close()
        self.cell_base.peak_feature.update_peak_features_by_run()
        connection.close()
        self.assertFalse(self.cell_base.peak_feature.objects.count())
        self.assertFalse(self.cell_base.peak_feature_instance.objects.count())
    
    def test_requires_reload(self):
        self.create_peak_table(sequencing_run_name='sample_run_1_h3k4me1', sequencing_run_type='ChIP-Seq')
        chr_1, start_1, end_1 = 5, 10000, 10200
        GlassPeak.objects.create(chromosome_id=chr_1,
                                start=start_1, end=end_1,
                                start_end=(start_1, end_1)
                                )
        source_1 = self._create_transcript(chr_1, 0, start_1-300, start_1)
        connection.close()
        run = SequencingRun.objects.get(source_table=GlassPeak._meta.db_table)
        run.requires_reload = True
        run.save()
        connection.close()
        self.cell_base.peak_feature.update_peak_features_by_run()
        connection.close()
        self.assertTrue(self.cell_base.peak_feature.objects.count())
        self.assertTrue(self.cell_base.peak_feature_instance.objects.count())
        