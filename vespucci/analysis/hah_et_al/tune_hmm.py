'''
Created on Jun 9, 2013

@author: karmel

From Hah et al:

"Tuning parameters include: (1) the shape (or variance) of emissions in the 
nontranscribed state, and (2) the probability of switching from a transcribed 
to a nontranscribed state. We calculated the sum of the two types of error 
described above over a two-dimensional grid, and took the parameter settings 
that minimized the sum of the errors. We evaluated model performance in 
cases where the shape setting was set to 5, 10, 15, or 20, and the -log of the 
transition probability between transcribed and nontranscribed was set to 
100, 150, 200, 250, 300, or 500. Final values selected by the model include 
a shape setting of 5 and a -log transition probability of 200."

R library is called GROseq, and is run from an R script here.
'''
from __future__ import division
import os
import sys
import pandas
import subprocess
from vespucci.analysis.hah_et_al.annotation_error import TranscriptEvaluator

class TranscriptComparer(object):
    reference = None
    def set_reference_data(self):
        '''
        Use mm9.bed as reference data for all comparisons.
        '''
        refseq = pandas.read_csv(self.refseq_path, header=0, sep='\t')
        
        # Bed has chr, start, end, ., ., strand
        refseq = refseq[[0,1,2,5]]
        refseq.columns = TranscriptEvaluator.colnames
        self.reference = refseq
        
    def eval_transcripts(self, data):
        '''
        For passed set of transcripts, evaluate using error
        methods defined in Hah et al. 
        '''
        evaluator = TranscriptEvaluator()
        evaluator.set_reference(self.reference)
        evaluator.set_target(data)
        return evaluator.get_summed_error()

    
class HMMTuner(TranscriptComparer):
    r_path = os.path.abspath('scripts/run_hmm.R')
    refseq_path = 'data/refseq_mm9.bed'
    data_path = 'data/input/notx_tags.txt'
    data_path = 'data/input/chr1_tags.sql.txt.clean'
    lts_probs = [-100, -150, -200, -250, -300]#, -500]
    uts = [5, 10, 15, 20, 25, 30]# 
        
    def loop_eval_hmm(self):
        '''
        Read in generated HMM transcript files and evaluate
        with summed error. Return error matrix.
        '''
        if not self.reference:
            self.set_reference_data()
            
        # Create error matrix, with uts as rows and lt_probs as cols
        rows = [pandas.Series([0], name=shape) for shape in self.uts]
        error_matrix = pandas.DataFrame(rows, columns=self.lts_probs)
        
        # Iterate through all parameters, m x n
        for prob in self.lts_probs:
            for shape in self.uts:
                path = 'data/output/hmm_transcripts_{}_{}.txt'.format(prob, shape)
                try: 
                    data = pandas.read_csv(path, sep='\t', header=None)
                    data = data[[0,1,2,5]]
                    data.columns = TranscriptEvaluator.colnames
    
                    error = self.eval_transcripts(data)
                    error_matrix[prob].ix[shape] = error
                except IOError:
                    # No file for this. Skip.
                    error_matrix[prob].ix[shape] = None
        return error_matrix
                
        
    def loop_run_hmm(self):
        '''
        Loop over set of parameters for -log transition prob and shape.
        Run HMM with m x n parameter possibilities.
        '''
        for prob in self.lts_probs:
            for shape in self.uts:
                self.run_hmm(prob, shape)
    
    def run_hmm(self, lt_prob, uts):
        ''' 
        Run R script with passed args. Output is saved in data dir.
        '''
        cmd = '{} --args "{}" {} {}'.format(self.r_path, 
                                          self.data_path,
                                          lt_prob, 
                                          uts)
        subprocess.check_call(cmd, 
                              shell=True)
    
if __name__ == '__main__':
    
    tuner = HMMTuner()
    if 'build' in sys.argv: tuner.loop_run_hmm()
    print tuner.loop_eval_hmm()