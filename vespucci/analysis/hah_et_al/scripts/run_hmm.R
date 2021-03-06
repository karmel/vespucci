#!/usr/bin/Rscript

library(GROseq)

# Get parameters
args = commandArgs(trailing=TRUE)
data_path = args[2]
lt_prob = as.integer(args[3])
uts = as.integer(args[4])
print(paste('Using LtProbB:', lt_prob, sep=' '))
print(paste('Using UTS:', uts, sep=' '))

# Get data
data = read.table(data_path, header=TRUE, sep='\t')

# Run HMM with passed params
hmm_tune = DetectTranscriptsEM(data, LtProbB=lt_prob, UTS=uts, thresh=1)

# Write out to data file.
write_path = paste('data/output/hmm_transcripts_',lt_prob,'_',uts,'.txt',sep='')
write.table(hmm_tune$Transcripts, file=write_path, sep='\t', 
			row.names=FALSE,col.names=FALSE, quote=FALSE, append=FALSE)
			
print(paste('Data saved to', write_path, sep=' '))