'''
We want to compare Vespucci generated transcripts to those
derived from Hah et al's HMM (groHMM). Here we set up methods to evaluate 
groHMM transcripts as per the Supp Methods in their paper:

Hah N, Danko CG, Core L, Waterfall JJ, Siepel A, Lis JT, Kraus WL. A rapid,
extensive, and transient transcriptional response to estrogen signaling in 
breast cancer cells. Cell. 2011 May 13;145(4):622-34.

"The two types of error are: (1) The fraction of genes that have two or more 
transcripts on the same strand end and start up again inside of a single gene 
annotation (in this case, the HMM is said to have 'broken up' a single 
annotation), and (2) The fraction of transcripts that continue between two 
nonoverlapping genes on the same strand (the HMM is said to 'run genes 
together')....our strategy was to choose a fixed set of tuning parameters 
that minimize the sum of these error types.  "

'''