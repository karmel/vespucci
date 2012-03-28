'''
Created on Mar 22, 2012

@author: karmel
'''
from pandas.io import parsers
from pandas.core.frame import DataFrame

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

    def collapse_strands(self, data):
        '''
        If the data is strand specific, we may want to collapse
        overlapping sense and antisense transcripts for motif finding.
        
        This is relevant in the case of eRNA, where transcription is 
        bidirectional, and we want the center of transcription.
        
        Testing:
        data = DataFrame({'chr_name': ['chr1', 'chr1', 'chr1','chr2','chr2',], 
                       'transcription_start': [0, 10, 21, 0, 5],
                       'transcription_end': [10, 20, 30, 10, 7], 
                       'strand': [0, 1, 0, 1, 0]},
                     )
        should yield
              chr_name strand transcription_end transcription_start
                0     chr1      0                20                   0
                2     chr1      0                30                  21
                3     chr2      1                10                   0

        '''
        compressed = []
        try: ordered = data.sort_index(by=['chr_name','transcription_start'])
        except KeyError: ordered = data.sort_index(by=['chromosome_id','transcription_start'])
        last = None
        for _, trans in ordered.iterrows():
            try:
                if trans['chr_name'] <= last['chr_name']\
                    and trans['transcription_start'] <= last['transcription_end']:
                        last['transcription_end'] = max(trans['transcription_end'],last['transcription_end'])
                        for key in last:
                            if key.find('tag_count') >= 0: last[key] += trans[key]
                else: 
                    compressed.append((last.name, last))
                    last = trans
            except TypeError: last = trans
        compressed.append((last.name, last))
            
        return DataFrame(dict(compressed)).transpose()