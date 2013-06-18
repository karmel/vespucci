'''
Created on Jun 11, 2013

@author: karmel

We want to calculate the error according to Hah et al
for Vespucci transcripts versus RefSeq, and for Vespucci
transcripts versus the Hah et al output.

'''

from __future__ import division
import pandas
from vespucci.analysis.hah_et_al.annotation_error import TranscriptEvaluator
from vespucci.analysis.hah_et_al.tune_hmm import TranscriptComparer


class HMMTuner(TranscriptComparer):
    refseq_path = 'data/refseq_mm9.bed'
    data_path = 'data/notx_vespucci.txt'
    
    def compare_to_refseq(self):
        '''
        Take Vespucci data for passed chromosome and calculate error versus
        RefSeq data.
        '''
        self.set_reference_data()
        data = self.get_data()
        
        error = self.eval_transcripts(data)
        return error
    
    def compare_vespucci_to_hmm(self, lt_prob=-200, uts=5):
        '''
        Take Vespucci data for passed chromosome and calculate error versus
        HMM transcripts for passed lt_prob and uts.
        '''
        path = 'data/output/hmm_transcripts_{}_{}.txt'.format(lt_prob, uts)
        hmm_data = pandas.read_csv(path, sep='\t', header=None)
        hmm_data = hmm_data[[0,1,2,5]]
        hmm_data.columns = TranscriptEvaluator.colnames

        self.reference = hmm_data
        data = self.get_data()
        
        error = self.eval_transcripts(data)
        return error
    
    def compare_hmm_to_vespucci(self, lt_prob=-200, uts=5):
        '''
        The reciprocal of compare_vespucci_to_hmm.
        Should return exactly the same value! Here we check...
        '''
        path = 'data/output/hmm_transcripts_{}_{}.txt'.format(lt_prob, uts)
        hmm_data = pandas.read_csv(path, sep='\t', header=None)
        hmm_data = hmm_data[[0,1,2,5]]
        hmm_data.columns = TranscriptEvaluator.colnames

        self.reference = self.get_data()
        
        error = self.eval_transcripts(hmm_data)
        return error
        
    def get_data(self):
        return pandas.read_csv(self.data_path, header=0, sep='\t')


if __name__ == '__main__':
    
    tuner = HMMTuner()
    print 'Error versus Refseq:'
    print tuner.compare_to_refseq()
    print 'Vespucci error versus HMM (-200, 5):'
    print tuner.compare_vespucci_to_hmm(-200, 5)
    print 'Vespucci error versus HMM (-200, 20):'
    print tuner.compare_vespucci_to_hmm(-200, 20)
    print 'Vespucci error versus HMM (-100, 5):'
    print tuner.compare_vespucci_to_hmm(-100, 5)
