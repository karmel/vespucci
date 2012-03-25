'''
Created on Mar 22, 2012

@author: karmel
'''
from pandas.io import parsers

class TranscriptAnalyzer(object):
    '''
    Using pandas, does some basic importing and filtering of transcript vectors.
    '''    
    
    def import_file(self, filename, separator='\t', header=True):
        if header: header_row = 0
        else: header_row = None
        data = parsers.read_csv(filename, sep=separator, header=header_row)
        
        return data
    
    def get_refseq(self, data, colname='has_refseq'):
        return data[data[colname] != 0]
    
    def normalize(self, data, colname, normfactor, suffix='_norm'):
        data[colname + suffix] = data[colname]*normfactor
        return data
    
    def get_gene_names(self, data, colname='gene_names'):
        return ','.join(data[colname].values).replace('{','').replace('}','')
