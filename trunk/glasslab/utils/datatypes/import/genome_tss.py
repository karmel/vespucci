'''
Created on Sep 24, 2010

@author: karmel

Script for importing original tab-delimited files for a genome
into models and DB tables.
'''
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.utils.datatypes.genome_reference import GenomeTSSFactory,\
    GeneIdentifier

def import_file(file_path='',genome=''):
    data = DelimitedFileParser(file_path).get_array()
    #tss_model = GenomeTSSFactory().get_genome_tss(genome)
    for row in data:
        try:
            '''
            record, created = tss_model.objects.get_or_create(gene_identifier=str(row[0]),
                                                               chromosome=str(row[1]),
                                                               start=int(row[2]),
                                                               end=int(row[3]),
                                                               direction=int(row[4]))
            '''
            record, created = GeneIdentifier.objects.get_or_create(genome=genome,
                                                                   gene_identifier=str(row[0]))
        except: 
            raise
        
if __name__ == '__main__':
    genome = 'mm9'
    import_file('/Volumes/Unknowme/homer/data/genomes/%s/%s.tss' % (genome,genome),genome)