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
import os
import sys


if __name__ == '__main__':
    learner = LogisticClassifier()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/classification'
    dirpath = learner.get_path(dirpath)
    
    
    # First time file setup
    data = get_data_with_bucket_score(learner, dirpath)
    # Get mean of all values to compress
    grouped_prelim = data.groupby('glass_transcript_id',as_index=False)
    grouped = grouped_prelim.mean()
    # Except for tag_count which should be summed.
    grouped['tag_count'] = grouped_prelim['tag_count'].sum()['tag_count']
    
    grouped.to_csv(learner.get_filename(dirpath,'feature_vectors.txt'),sep='\t',index=False)
    
    raise Exception
    grouped = learner.import_file(learner.get_filename(dirpath, 'feature_vectors.txt'))
    
    if False:
        # Can we predict pausing ratio?
        
        # Minimal ratio in KLA+Dex vs. KLA pausing
        try: min_ratio= float(sys.argv[1])
        except IndexError: min_ratio = 1.5 
        try: min_diff = float(sys.argv[2])
        except IndexError: min_diff = .05
        try: force_choice = sys.argv[3].lower() == 'force'
        except IndexError: force_choice = False
        try: extra_dir = sys.argv[4]
        except IndexError: extra_dir = ''
        
        subdir = learner.get_filename(dirpath, 
                    extra_dir, 'pausing_ratio_diff_{0}_{1}'.format(
                        str(min_ratio).replace('.','_'),str(min_diff).replace('.','_')))
        if force_choice: subdir = subdir + '_forced_choice'
        
        if not os.path.exists(subdir): os.makedirs(subdir)
        
        pausing_states = grouped.filter(regex=r'(kla_dex_\d_bucket_score|kla_dex_bucket_score)')
            
        for replicate_id in ('', 1, 2, 3, 4):
            rep_str = get_rep_string(replicate_id)
            # First do some column cleanup..
            # Remove cols that are the kla_dex_bucket target; or that are not from the current replicate;
            # or that are id fields
            regex = r'(?!(kla_dex_\d_bucket_score|kla_dex_bucket_score))' +\
                            r'(({1}pu_1_kla)|{0})'.format('(?!(.*_\d_.*|.*_id))', rep_str and r'.*' + rep_str + r'.*|' or '')
            dataset = grouped.filter(regex=regex)
        
            
            labels = pausing_states['kla_dex_{0}bucket_score'.format(rep_str)] \
                                /dataset['kla_{0}bucket_score'.format(rep_str)] >= min_ratio
            
            labels_2 = pausing_states['kla_dex_{0}bucket_score'.format(rep_str)] \
                                - dataset['kla_{0}bucket_score'.format(rep_str)] >= min_diff
            labels = map(lambda x: int(x[0] and x[1]), zip(labels, labels_2))
            print 'Total positive examples: ', sum(labels)
            # Nulls should be zeroes. Fill those first.
            dataset = dataset.fillna(0)
            dataset = learner.normalize_data(dataset)
            
            
            best_err = 1.0
            best_c = 0
            best_chosen = []
            possible_k = [20, 10, 5, 2]
            for k in possible_k:
                if force_choice:
                    #chosen = ['kla_{0}bucket_score'.format(rep_str), 'dmso_{0}bucket_score'.format(rep_str)]
                    chosen = ['cebpa','cebpa_kla']
                else:
                    chosen = learner.get_best_features(dataset, labels, k=k)
                
                num_features = len(chosen)
                
                err, c = learner.run_nested_cross_validation(dataset, labels, columns=chosen,
                            draw_roc=True, draw_decision_boundaries=force_choice,
                            title_suffix=replicate_id and 'Group {0}'.format(replicate_id) or 'Overall',
                            save_path_prefix=learner.get_filename(subdir,'plot_{0}group'.format(rep_str)),
                        )
                
                if err < best_err:
                    best_err = err
                    best_c = c
                    best_chosen = chosen
                    
                if force_choice: break
        
            print "Best number of features: ", len(best_chosen)
            print "Best features: ", best_chosen
            print "Best C, MSE: ", best_c, best_err
    if True:
        # How about transrepression?
        try: force_choice = sys.argv[1].lower() == 'force'
        except IndexError: force_choice = False
        try: extra_dir = sys.argv[2]
        except IndexError: extra_dir = ''
        
        subdir = learner.get_filename(dirpath, 
                    extra_dir, 'transrepression')
        if force_choice: subdir = subdir + '_forced_choice'
        
        if not os.path.exists(subdir): os.makedirs(subdir)
        
            
        for replicate_id in ('', 1, 2, 3, 4):
            rep_str = get_rep_string(replicate_id)
            
            dataset = grouped[grouped['kla_{0}state'.format(rep_str)] == 1].reset_index()
            targets = dataset.filter(regex=r'.*_state')    
            dataset = dataset.filter(regex=r'(?!(.*state|.*id))')
            
            
            labels = targets['kla_{0}state'.format(rep_str)] == 1
            labels_2 = targets['dex_over_kla_{0}state'.format(rep_str)] == -1
            
            labels = map(lambda x: int(x[0] and x[1]), zip(labels, labels_2))
            print 'Total examples, positive: ', len(dataset), sum(labels)
            # Nulls should be zeroes. Fill those first.
            dataset = dataset.fillna(0)
            dataset = learner.normalize_data(dataset)
            
            
            best_err = 1.0
            best_c = 0
            best_chosen = []
            possible_k = [20, 10, 5, 2]
            for k in possible_k:
                if force_choice:
                    chosen = ['', 'kla_{0}bucket_score'.format(rep_str)]
                    #chosen = ['kla_{0}bucket_score'.format(rep_str), 'tag_count']
                else:
                    #chosen = learner.get_best_features(dataset, labels, k=k)
                    chosen = ['kla_{0}bucket_score'.format(rep_str), 'dmso_{0}bucket_score'.format(rep_str),
                              'gr_dex','cebpa_kla']
                num_features = len(chosen)
                
                err, c = learner.run_nested_cross_validation(dataset, labels, columns=chosen,
                            draw_roc=True, draw_decision_boundaries=force_choice,
                            title_suffix=replicate_id and 'Group {0}'.format(replicate_id) or 'Overall',
                            save_path_prefix=learner.get_filename(subdir,'plot_{0}group'.format(rep_str)),
                        )
                
                if err < best_err:
                    best_err = err
                    best_c = c
                    best_chosen = chosen
                    
                if force_choice: break
        
            print "Best number of features: ", len(best_chosen)
            print "Best features: ", best_chosen
            print "Best C, MSE: ", best_c, best_err

            
            
        