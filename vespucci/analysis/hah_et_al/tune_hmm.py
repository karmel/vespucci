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

class HMMTuner(object):
    r_path = os.path.abspath('scripts/run_hmm.R')
    lts_probs = [50, 100, 150, 200, 250, 300, 500]
    uts = [1, 5, 10, 15, 20]
    
    
    def loop_hmm(self):
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
                                                       uts), shell=True)
    
if __name__ == '__main__':
    
    tuner = HMMTuner()
    tuner.run_hmm(100, 10)