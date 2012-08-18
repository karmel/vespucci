'''
Created on Jul 4, 2012

@author: karmel

The goal here is to see if we can tease out which features are 
predictive of characteristics of interest, such as pausing ratio
or transrepression. Worth a stab.
'''
from glasslab.dataanalysis.misc.gr_project_2012.elongation import get_rep_string
import sys
from glasslab.dataanalysis.motifs.motif_analyzer import MotifAnalyzer


if __name__ == '__main__':
    yzer = MotifAnalyzer()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/motifs'
    dirpath = yzer.get_path(dirpath)
    
    grouped = yzer.import_file(yzer.get_filename(dirpath, 'feature_vectors.txt'))
    
    trans = []
    if True:
        # Minimal ratio in KLA+Dex vs. KLA pausing
        try: min_ratio= float(sys.argv[1])
        except IndexError: min_ratio = -1
        try: 
            try: secondary_min_ratio= float(sys.argv[2])
            except ValueError: secondary_min_ratio= sys.argv[2]
        except IndexError: secondary_min_ratio = 'none'
        try: thresh = int(sys.argv[3])
        except IndexError: thresh = 2
        
        grouped['relevant_sets'] = 0
        
        rep_ids = (1, 2, 3, 4)
        for replicate_id in rep_ids:
            rep_str = get_rep_string(replicate_id)
            
            
            primary_min = grouped['kla_{0}gene_body_lfc'.format(rep_str)] <= min_ratio
            
            if secondary_min_ratio != 'none':
                secondary_min = grouped['dex_over_kla_{0}gene_body_lfc'.format(rep_str)] >= secondary_min_ratio
            else: 
                secondary_min = True
            
            trans_set = grouped.ix[primary_min & secondary_min]['glass_transcript_id'].values.tolist()
            grouped['relevant_sets'] += (primary_min & secondary_min).apply(int)
            
            trans.append(trans_set)
            
            print 'Genes with rep {0} KLA LFC <= {1} and Dex over KLA LFC >= {2}:'.format(
                                    rep_str, min_ratio, secondary_min_ratio), len(trans_set)
            
            
        
        
        print 'Derepressed in at least 4 reps:', sum(grouped['relevant_sets'] >= 4)
        print 'Derepressed in at least 3 reps:', sum(grouped['relevant_sets'] >= 3)
        print 'Derepressed in at least 2 reps:', sum(grouped['relevant_sets'] >= 2)
        print 'Derepressed in at least 1 reps:', sum(grouped['relevant_sets'] >= 1)
        
        
        # For motif finding
        data = yzer.import_file(yzer.get_filename(dirpath, 'transcript_vectors.txt'))
        
        ids = grouped[grouped['relevant_sets'] >= thresh]['glass_transcript_id']
        dataset = data[data['id'].isin(ids)]
        if True:
            all_data = data[data['id'].isin(grouped['glass_transcript_id'])]
            yzer.prep_files_for_homer(all_data, 'all_transcripts_preceding'.format(thresh), 
                                          yzer.get_filename(dirpath, 'from_genes'), 
                                          center=False, reverse=False, preceding=True, size=200)
            yzer.prep_files_for_homer(all_data, 'all_transcripts_promoter'.format(thresh), 
                                          yzer.get_filename(dirpath, 'from_genes'), 
                                          center=False, reverse=False, preceding=False, size=200)
        if False:
            yzer.prep_files_for_homer(dataset, 'derepressed_in_{0}_kla_{1}_dex_over_kla_{2}_promoter_200'.format(
                                                    thresh, min_ratio, secondary_min_ratio), 
                                          yzer.get_filename(dirpath,'from_genes','derepressed'), 
                                          center=False, reverse=False, preceding=False, size=200)
            yzer.prep_files_for_homer(dataset, 'derepressed_in_{0}_kla_{1}_dex_over_kla_{2}_preceding_200'.format(
                                                    thresh, min_ratio, secondary_min_ratio), 
                                          yzer.get_filename(dirpath,'from_genes','derepressed'), 
                                          center=False, reverse=False, preceding=True, size=200)