'''
Created on Sep 24, 2010

@author: karmel

Script for importing original tab-delimited files for a genome
into models and DB tables.
'''
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.utils.datatypes.genome_reference import GeneDetail,\
    GeneIdentifier

def import_file(file_path='',genome=''):
    data = DelimitedFileParser(file_path).get_array()
    for row in data:
        try:
            if row[0] == 'GeneID' or not row[2]: continue
            ident, created = GeneIdentifier.objects.get_or_create(genome=genome,
                                                                   gene_identifier=str(row[2]))
            record, created = GeneDetail.objects.get_or_create(gene_identifier=ident,
                                                               unigene_identifier=str(row[1]),
                                                               ensembl_identifier=str(row[3]),
                                                               gene_name=str(row[4]),
                                                               gene_alias=str(row[5]),
                                                               gene_description=str(row[8]))
            
            
        except: 
            raise
        
if __name__ == '__main__':
    genome = 'hg18r'
    import_file('/Volumes/Unknowme/homer/data/accession/human.description',genome)