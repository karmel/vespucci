#!/usr/bin/Rscript

library(GROseq)

# Get parameters
args = commandArgs(trailing=TRUE)
lt_prob = args[1]
uts = args[2]

# Get data
data_path = '../data/notx_chrX.txt'
data = read.table(data_path, header=TRUE, sep='\t')

# Run HMM with passed params
hmm_tune = DetectTranscriptsEM(data, LtProbB=lt_prob, UTS=uts, thresh=1)

# Write out to data file.
write_path = paste('../data/hmm_transcripts_',lt_prob,'_',uts,'.txt',sep='')
write.table(hmm_tune$Transcripts, file=write_path, sep='\t', 
			row.names=FALSE,col.names=TRUE)
			
print(paste('Data saved to', write_path, sep=' '))