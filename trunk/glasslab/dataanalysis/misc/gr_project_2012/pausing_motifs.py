'''
Created on Jul 5, 2012

@author: karmel
'''
from glasslab.dataanalysis.motifs.motif_analyzer import MotifAnalyzer
from glasslab.dataanalysis.misc.gr_project_2012.elongation import get_rep_string
import sys


if __name__ == '__main__':
    yzer = MotifAnalyzer()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/pausing_ratio_motifs'
    dirpath = yzer.get_path(dirpath)

    pausing_data = yzer.import_file(yzer.get_filename(dirpath, 'feature_vectors.txt'))
    data = yzer.import_file(yzer.get_filename(dirpath, 'transcript_vectors.txt'))
    
    try: min_ratio= float(sys.argv[1])
    except IndexError: min_ratio = 1.5 
        
    if False:
        yzer.prep_files_for_homer(data, 'all_transcripts_preceding', dirpath, 
                                  center=False, reverse=False, preceding=True, size=200)
    
    
    for replicate_id in ('', 1, 2, 3, 4):
        rep_str = get_rep_string(replicate_id)
        key = 'kla_dex_{0}pausing_ratio'.format(rep_str)
        pausing_data[key] = pausing_data['kla_dex_{0}bucket_score'.format(rep_str)] \
                            /pausing_data['kla_{0}bucket_score'.format(rep_str)]
        pausing_data = pausing_data.fillna(0)
        
        pausing_ids = pausing_data[pausing_data[key] >= min_ratio]['glass_transcript_id']
        dataset = data[data['id'].isin(pausing_ids)]
        
        print len(dataset)
        
        if True:
            yzer.prep_files_for_homer(dataset, 'paused_{0}_{1}preceding_200'.format(min_ratio, rep_str), 
                                      dirpath, 
                                      center=False, reverse=False, preceding=True, size=200)