'''
Created on Feb 16, 2011

@author: karmel

In order to compare several different gap thresholds, we want to 
create an ROC-like-graph, analyzing the true/false positive/negative
rates of the Glass Atlas in calling RefSeq transcripts.

This is intended to serve as one of a number of criteria in
evaluating parameters, as the "classification" and even truth value
being compared against are not set in stone. 
'''
from __future__ import division
from django.db import models, connection
from glasslab.config import current_settings
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from matplotlib import pyplot
from random import choice

class ParameterPerformance(models.Model):
    '''
    Model for storing, for each "classifier" (gap threshold),
    and each target (RefSeq trans), whether the classifier
    got a true positive, false positive, true negative, or false negative.
    
    The guesses are evaluated according to:
    for each of the refseq trans in the glass_atlas_ref_thiomac database 
    (which is a database constructed from all unique regions in the RefSeq and ncRNA.org
    databases):
        
        * TP if refseq score >= 15 and is more than 50% covered by trans with score <=15
        * TN if refseq score <= 15 and is less than 50% covered by trans with score <=15
        * FP if refseq score <= 15 and is more than 50% covered by trans with score <=15
        * FN if refseq score >= 15 and is less than 50% covered by trans with score <=15
    
    Note that the score of the RefSeq transcripts was set according to the following::
        
        If transcript has wt notx polII serine 5 peak within (half of trans length) of start site:
            set score = 15
    
    '''
    db_choices  = ('ref',#'gap_0', 'gap_5', 'gap_10', 'gap_20', 'gap_25', 'gap_50', 'gap_100', 'gap_200',
                   #'gap2_0', 'gap2_25', 'gap2_50', 'gap2_50_no_ext', 'gap2_100', 'gap2_200', 'gap2_1000',
                   )
    
    cell_base = CellTypeBase().get_cell_type_base(current_settings.CURRENT_CELL_TYPE)()
    
    db_version              = models.CharField(max_length=50, choices=[(x,x) for x in db_choices])
    refseq_transcript_id    = models.IntegerField(max_length=10)
    within_refseq           = models.BooleanField(default=False)
    true_positive           = models.IntegerField(max_length=1)
    false_positive          = models.IntegerField(max_length=1)
    true_negative           = models.IntegerField(max_length=1)
    false_negative          = models.IntegerField(max_length=1)
    score                   = models.FloatField()
    
    class Meta:
        db_table    = 'glass_atlas_%s"."parameter_performance' % current_settings.REFERENCE_GENOME

    @classmethod
    def analyze_all_transcripts(cls):
        '''
        For each transcript in the RefSeq/ncRNA DB, determine how each of 
        the gap threshold DBs do at "calling" the transcript.
        '''
        glass_transcript = cls.cell_base.glass_transcript
        # First, get all PolII Serine5 peaks
        glass_transcript.reset_table_name(genome='ref') 
        ref_transcripts = list(glass_transcript.objects.filter(score__gte=15).order_by('?')[:10])
        
        # For each parameter tested, evaluate whether the ref transcript was 
        # appropriately called.   
        for db_version in cls.db_choices:
            glass_transcript.reset_table_name(genome=db_version)
            for ref in ref_transcripts:
                # Check whole trans
                length = ref.transcription_end - ref.transcription_start
                start_1 = ref.strand and (ref.transcription_end - length) or ref.transcription_start
                end_1 = ref.strand and ref.transcription_end or (ref.transcription_start + length)
                # First check refseq trans
                cls.call_transcript(glass_transcript, db_version, start_1, end_1, ref, True)
                
                # Then check end segment after transcript as a true negative
                start_2 = ref.strand and (ref.transcription_start - (length+500)) or (ref.transcription_end + 500)
                end_2 = ref.strand and (ref.transcription_start - 500) or (ref.transcription_end + (length+500))
                cls.call_transcript(glass_transcript, db_version, start_2, end_2, ref, False)
                    
    @classmethod 
    def call_transcript(cls, glass_transcript, db_version, start, end, ref, within_refseq):
        verdict = 1
        # Set up where clause
        #ref_fragment = max(1000, int((ref.transcription_end - ref.transcription_start)/2))
        where = ['start_end && public.make_box(%d, 0, %d, 0)' % (start, end)]
        matching = list(glass_transcript.objects.filter(chromosome=ref.chromosome, 
                                    strand=ref.strand, score__gte=15).extra(where=where).order_by('transcription_start'))

        # Also, if this is not within the selected refseq trans, check for another trans, just in case this is a Positive
        if not within_refseq:
            glass_transcript.reset_table_name(genome='ref')
            other_ref = list(glass_transcript.objects.filter(chromosome=ref.chromosome, 
                                    strand=ref.strand, score__gte=15).extra(where=where))
            glass_transcript.reset_table_name(genome=db_version)
            if other_ref: return
            
        # Too many transcripts?
        if len(matching) == 0: verdict = 0
        elif len(matching) > 10: verdict = 0
    
        # Determine coverage
        covered = sum([min(match.transcription_end, end) 
                       - max(match.transcription_start, start) for match in matching])
        #if covered/(end - start) < .5: verdict = 0
        
        # Store result
        record, created = cls.objects.get_or_create(db_version=db_version, 
                                                    refseq_transcript_id=ref.id, within_refseq=within_refseq)
        record.score = covered/(end - start)
        if ref.score >= 15 and within_refseq: 
            record.true_negative, record.false_positive = 0, 0
            if verdict: record.true_positive, record.false_negative = 1, 0
            else:       
                record.true_positive, record.false_negative = 0, 1
        else:
            record.true_positive, record.false_negative = 0, 0
            if verdict: record.false_positive, record.true_negative = 1, 0
            else:       record.false_positive, record.true_negative = 0, 1
        record.save()
        connection.close()
        
    @classmethod
    def draw_roc(cls):
        '''
        Draw an ROC graph based on values stored for each db_version.
        
        Modeled after Algorithm 1 in https://cours.etsmtl.ca/sys828/REFS/A1/Fawcett_PRL2006.pdf
        '''
        # Set up pyplot
        pyplot.figure(figsize=(8,12))
        pyplot.title('ROC: Gap Threshold Comparisons')
        pyplot.xlabel('False positive rate')
        pyplot.ylabel('True positive rate')
        
        positive_count = cls.objects.filter(db_version='ref',true_positive=1).count()
        negative_count = cls.objects.filter(db_version='ref',true_negative=1).count()
        # Get truth values
        for db_version in cls.db_choices:
            # Initialize x and y vals
            #print db_version
            fp_rate, tp_rate = [], []
            
            area = 0
            last_fp_count, last_tp_count = 0, 0
            fp_count, tp_count = 0, 0
            last_val = None
            guesses = cls.objects.filter(db_version=db_version).order_by('-score')
            for guess in guesses:
                if guess.score != last_val: 
                    #print guess.score, fp_count, tp_count
                    fp_rate.append(fp_count/negative_count)
                    tp_rate.append(tp_count/positive_count)
                    
                    area += cls.trapezoid_area(last_fp_count,fp_count,last_tp_count,tp_count)
                    
                    last_val = guess.score
                    last_fp_count, last_tp_count = fp_count, tp_count
                    
                real_label = cls.objects.get(db_version='ref', 
                                                refseq_transcript_id=guess.refseq_transcript_id,
                                                within_refseq=guess.within_refseq)
                if real_label.true_positive: tp_count += 1
                if real_label.true_negative: fp_count += 1
                
            # Finally, (1,1)
            fp_rate.append(fp_count/negative_count)
            tp_rate.append(tp_count/positive_count)
            area += cls.trapezoid_area(last_fp_count,negative_count,last_tp_count,positive_count)
            area = area/(negative_count*positive_count) # Scale from PxN to unit square
            
            # Add labeled line to pyplot
            label = '%s (AUC: %.3f)' % (db_version, area)
            pyplot.plot(fp_rate, tp_rate, choice(['-','--','-.',':']), label=label)
        pyplot.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=1, ncol=3, mode="expand", borderaxespad=0.)
        pyplot.savefig('/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Glass Atlas/parameter_determination_2011_01_28/pyplot/roc_comparison.png')

    @classmethod
    def trapezoid_area(cls, x1, x2, y1, y2):
        return abs(x2 - x1)*((y2 + y1)/2)
    