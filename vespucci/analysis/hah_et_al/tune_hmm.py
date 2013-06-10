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
import subprocess
from vespucci.analysis.hah_et_al.annotation_error import TranscriptEvaluator
from vespucci.utils.scripting import get_vespucci_path
import pandas

class HMMTuner(object):
    r_path = os.path.abspath('scripts/run_hmm.R')
    lts_probs = [50, 100,]# 150, 200, 250, 300, 500]
    uts = [1, 5, ] #10, 15, 20]
    reference = None    
        
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
                data = pandas.read_csv(path, sep='\t', header=None)
                data = data[[0,1,2,5]]
                data.columns = TranscriptEvaluator.colnames
                print data.columns
                print data.head()
                error = self.eval_transcripts(data)
                error_matrix[prob].ix[shape] = error
        print error_matrix
                
    def set_reference_data(self):
        '''
        Use mm9.bed as reference data for all comparisons.
        '''
        path_to_file = os.path.join(get_vespucci_path(),
                       'genomereference/pipeline/data/mm9/mm9.bed')
        refseq = pandas.read_csv(path_to_file, header=None, sep='\t')
        
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
        subprocess.check_call('{} --args {} {}'.format(self.r_path, 
                                                       lt_prob, 
                                                       uts), 
                              shell=True)
    
if __name__ == '__main__':
    
    tuner = HMMTuner()
    #tuner.loop_run_hmm()
    tuner.loop_eval_hmm()