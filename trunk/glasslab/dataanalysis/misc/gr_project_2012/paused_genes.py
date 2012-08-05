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
    
    paused = []
    if True:
        # Can we predict pausing ratio?
        
        # Minimal ratio in KLA+Dex vs. KLA pausing
        try: min_ratio= float(sys.argv[1])
        except IndexError: min_ratio = 2 
        try: secondary_min_ratio= float(sys.argv[2])
        except IndexError: secondary_min_ratio = 1.2
        
        grouped['relevant_sets_primary'] = 0
        grouped['relevant_sets_secondary'] = 0
        
        rep_ids = (1, 2, 3, 4)
        for replicate_id in rep_ids:
            rep_str = get_rep_string(replicate_id)
            
            
            grouped['rep_{0}pausing_ratio_ratio'.format(rep_str)] = \
                            grouped['kla_dex_{0}bucket_score'.format(rep_str)] \
                                /grouped['kla_{0}bucket_score'.format(rep_str)]
            
            primary_min = grouped['rep_{0}pausing_ratio_ratio'.format(rep_str)] >= min_ratio
            
            secondary_min = grouped['rep_{0}pausing_ratio_ratio'.format(rep_str)] >= secondary_min_ratio
            
            
            trans_1 = grouped['kla_{0}gene_body_lfc'.format(rep_str)] >= 2
            trans_2 = grouped['dex_over_kla_{0}gene_body_lfc'.format(rep_str)] <= -.58
            
            paused_set = grouped.ix[primary_min & trans_2]['glass_transcript_id'].values.tolist()
            paused.append(paused_set)
            
            print 'Genes with rep_{0}pausing_ratio_ratio >= {1}:'.format(rep_str, min_ratio), len(paused_set)
            
            grouped['relevant_sets_primary'] += (primary_min & trans_2).apply(int)
            grouped['relevant_sets_secondary'] += secondary_min.apply(int)
            
        
        
        print 'Assuming pausing_ratio_ratio is at least {0}...'.format(secondary_min_ratio)
        
        grouped = grouped[grouped['relevant_sets_secondary'] == 4]
        print 'Genes that have a pausing_ratio_ratio of at least {0} in all 4 reps:'.format(
                            secondary_min_ratio), len(grouped)
        
        print 'Paused in at least 4 reps:', sum(grouped['relevant_sets_primary'] >= 4)
        print 'Paused in at least 3 reps:', sum(grouped['relevant_sets_primary'] >= 3)
        print 'Paused in at least 2 reps:', sum(grouped['relevant_sets_primary'] >= 2)
        print 'Paused in at least 1 reps:', sum(grouped['relevant_sets_primary'] >= 1)
        
        means = grouped[['rep_1_pausing_ratio_ratio','rep_2_pausing_ratio_ratio',
                       'rep_3_pausing_ratio_ratio','rep_4_pausing_ratio_ratio']].mean(axis=1)
        print 'Paused in the average of all reps:', sum(means >= min_ratio)
        
        # For motif finding
        peak_type = 'p65_kla_dex'
        data = yzer.import_file(yzer.get_filename(dirpath, 'from_peaks/{0}_promoter_vectors.txt'.format(peak_type)))
        data['id'] = data['peak_id']
        
        thresh = 2
        ids = grouped[grouped['relevant_sets_primary'] >= thresh]['glass_transcript_id']
        dataset = data[data['glass_transcript_id'].isin(ids)]
        
        if True:
            yzer.prep_files_for_homer(data, 'all_{0}_200'.format(peak_type), 
                                      yzer.get_and_create_path(dirpath,'from_peaks',peak_type), 
                                      center=True, reverse=False, preceding=False, size=200)
        
        yzer.prep_files_for_homer(dataset, 'paused_in_{0}_at_least_{1}_min_{2}_down_in_dex_{3}_200'.format(thresh, 
                                                    min_ratio, secondary_min_ratio, peak_type), 
                                      yzer.get_and_create_path(dirpath,'from_peaks',peak_type), 
                                      center=True, reverse=False, preceding=False, size=200)
        