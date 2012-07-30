'''
Created on Jul 10, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer

if __name__ == '__main__':
    yzer = TranscriptAnalyzer()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/'
    dirpath = yzer.get_path(dirpath)
    
    data = yzer.import_file(yzer.get_filename(dirpath, 'transcript_vectors.txt'))
    
    egr2 = yzer.import_file(yzer.get_filename(dirpath, 'egr2_analysis_2012_07','egr2_peaks_annotated_hg19.txt'))
    
    data = data.fillna(0)
    #data = data[(data['gr_dex_tag_count'] == 0)]
    #data = data[(data['p65_kla_dex_tag_count'] > 0)]
    data = data[(data['refseq'] == 't')]
    not_trans = data[(data['kla_3_lfc'] >= 1) & (data['dex_over_kla_3_lfc'] > -.58)]
    transrepressed = data[(data['kla_3_lfc'] >= 1) & (data['dex_over_kla_3_lfc'] <= -.58)]
    
    # Get peaks actually in genes
    egr2_genes = egr2[egr2.apply(lambda row: len([term for term in ('promoter','exon','UTR') 
                                                    if str(row['Annotation']).find(term) >= 0]) > 0, axis=1)]
    gene_names = map(lambda x: str(x).lower(), egr2_genes['Gene Name'])
    
    total_data = len(not_trans)
    total_transrepressed = len(transrepressed)
    
    
    def condition_1(row):
        other = True #row['cebpa_tag_count'] > 0
        names = str(row['gene_names']).lower().strip('{').strip('}').split(',')
        return other and len([name for name in names if name in gene_names]) > 0
    
    
    for i, f in enumerate((condition_1,)):
        print '\n\n\nFor condition: ', i 
        count_data = len(not_trans[not_trans.apply(f,axis=1)])
        count_transrepressed = len(transrepressed[transrepressed.apply(f,axis=1)])
        print 'Total count, fraction: ', count_data, count_data/total_data 
        print 'Transrepressed count, fraction: ', count_transrepressed, count_transrepressed/total_transrepressed
        #print data[(data['dex_over_kla_1_lfc'] > 0)]['glass_transcript_id'][100:200]
        #print transrepressed['glass_transcript_id'][100:200]