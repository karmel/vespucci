library(GROseq)

# Get refseq data
ref_path = '../../../genomereference/pipeline/data/mm9/mm9.bed'
ref = read.table(ref_path, header=FALSE, sep="\t")

#