'''
Created on Jun 9, 2013

@author: karmel

From Hah et al:

"Tuning parameters include: (1) the shape (or variance) of emissions in the 
nontranscribed state, and (2) the probability of switching from a transcribed 
to a nontranscribed state. We calculated the sum of the two types of error 
described above over a two-dimensional grid, and took the parameter settings 
that minimized the sum of the errors. We evaluated model performance in 
cases where the shape setting was set to 5, 10, 15, or 20, and the –log of the 
transition probability between transcribed and nontranscribed was set to 
100, 150, 200, 250, 300, or 500. Final values selected by the model include 
a shape setting of 5 and a –log transition probability of 200."

R library is called GROseq, and is run from an R script here.
'''

class HMMTuner(object):
    r_path = 'scripts/run_hmm.R'
    lts_probs = [50, 100, 150, 200, 250, 300, 500]
    uts = [1, 5, 10, 15, 20]
    
    