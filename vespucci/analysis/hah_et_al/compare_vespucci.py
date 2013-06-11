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
    
    def compare_to_refseq(self, chr='chr1'):
        '''
        Take Vespucci data for passed chromosome and calculate error versus
        RefSeq data.
        '''
        self.set_reference_data()
        data = self.get_data(chr)
        
        error = self.eval_transcripts(data)
        print error
        
    def get_data(self, chr='chr1'):
        data = pandas.read_csv(self.data_path, header=0, sep='\t')
        data = data[data['chr'] == chr]
        return data
    
if __name__ == '__main__':
    
    tuner = HMMTuner()
    tuner.compare_to_refseq()