'''
Created on Jul 4, 2012

@author: karmel

The goal here is to see if we can tease out which features are 
predictive of characteristics of interest, such as pausing ratio
or transrepression. Worth a stab.
'''
from glasslab.dataanalysis.misc.gr_project_2012.width_buckets import get_data_with_bucket_score
from glasslab.dataanalysis.machinelearning.logistic_classifier import LogisticClassifier
from glasslab.dataanalysis.misc.gr_project_2012.elongation import get_rep_string


if __name__ == '__main__':
    learner = LogisticClassifier()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/classification'
    dirpath = learner.get_path(dirpath)
    
    data = get_data_with_bucket_score(learner, dirpath)
    # Get mean of all values to compress
    grouped_prelim = data.groupby('glass_transcript_id',as_index=False)
    grouped = grouped_prelim.mean()
    # Except for tag_count which should be summed.
    grouped['tag_count'] = grouped_prelim['tag_count'].sum()['tag_count']
    
    if True:
        # Can we predict pausing ratio?
        
        subdir = 'pausing_ratio_diff'
        # First do some column cleanup.
        pausing_states = grouped.filter(regex=r'(kla_dex_\d_bucket_score|kla_dex_bucket_score)')
        dataset = grouped.filter(regex=r'(?!^(kla_dex_\d_bucket_score|kla_dex_bucket_score))')
        
        margin = .05 # Minimal diff in KLA+Dex vs. KLA pausing
        
        for replicate_id in ('', 1, 2, 3, 4):
            rep_str = get_rep_string(replicate_id)
            labels = map(int, pausing_states['kla_dex_{0}bucket_score'.format(rep_str)] \
                                - dataset['kla_{0}bucket_score'.format(rep_str)] >= margin)
            
            dataset = learner.normalize_data(dataset)
            
            
            best_err = 1.0
            best_c = 0
            best_chosen = []
            possible_k = [20,10,5]
            for k in possible_k:
                chosen = learner.get_best_features(data, labels, k=k)
                err, c, for_roc = learner.run_nested_cross_validation(dataset, labels, chosen)
                learner.draw_roc(for_roc, 
                     title='ROC for k = {1}, c = {2}, {0}'.format(
                            replicate_id and 'Group {0}'.format(replicate_id) or 'Overall', k, c), 
                     save_path=learner.get_filename(dirpath, subdir, 
                            'ROC_{0}group_k_{1}_c_{2}.png'.format(rep_str, k, c)), 
                     show_plot=False)
                if err < best_err:
                    best_err = err
                    best_c = c
                    best_chosen = chosen
        
        
            print "Best number of features: ", len(chosen)
            print "Best features: ", best_chosen
            print "Best C, MSE: ", best_c, best_err

            
            
        