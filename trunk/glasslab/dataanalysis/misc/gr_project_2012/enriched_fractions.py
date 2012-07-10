'''
Created on Jul 6, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer

if __name__ == '__main__':
    yzer = TranscriptAnalyzer()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/'
    dirpath = yzer.get_path(dirpath)
    
    data = yzer.import_file(yzer.get_filename(dirpath, 'transcript_vectors.txt'))
    
    data = data.fillna(0)
    #data = data[(data['p65_kla_dex_tag_count'] >= 100)]
    data = data[(data['kla_1_lfc'] >= 1)]
    transrepressed = data[(data['kla_1_lfc'] >= 1) & (data['dex_over_kla_1_lfc'] <= -.58)]
    
    total_data = len(data)
    total_transrepressed = len(transrepressed)
    
    
    def condition_1(row):
        return (#row['distal'] == 't'
                row['gr_kla_dex_tag_count'] > 50
                and row['cebpa_kla_tag_count'] < 50
                #row['p65_kla_tag_count'] == 0
                #row['p65_kla_dex_tag_count'] > 50
                #and row['gr_dex'] == 0
                #and row['gr_kla_dex'] == 1
                )
    for i, f in enumerate((condition_1,)):
        print '\n\n\nFor condition: ', i 
        count_data = len(data[data.apply(f,axis=1)])
        count_transrepressed = len(transrepressed[transrepressed.apply(f,axis=1)])
        print 'Total count, fraction: ', count_data, count_data/total_data 
        print 'Transrepressed count, fraction: ', count_transrepressed, count_transrepressed/total_transrepressed
        #print data[(data['dex_over_kla_1_lfc'] > 0)]['glass_transcript_id'][100:200]
        #print transrepressed['glass_transcript_id'][100:200]