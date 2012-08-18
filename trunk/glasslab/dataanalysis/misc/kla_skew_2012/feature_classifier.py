'''
Created on Jul 4, 2012

@author: karmel

The goal here is to see if we can tease out which features are 
predictive of characteristics of interest, such as pausing ratio
or transrepression. Worth a stab.
'''
from glasslab.dataanalysis.machinelearning.logistic_classifier import LogisticClassifier
from glasslab.dataanalysis.misc.gr_project_2012.elongation import get_rep_string
import os
import sys

if __name__ == '__main__':
    learner = LogisticClassifier()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/KLA skew'
    dirpath = learner.get_path(dirpath)
    grouped = learner.import_file(learner.get_filename(dirpath, 'feature_vectors.txt'))
    
                
    if True:
        # Can we predict repression?
        try: force_choice = sys.argv[1].lower() == 'force'
        except IndexError: force_choice = False
        try: extra_dir = sys.argv[2]
        except IndexError: extra_dir = ''
        
        subdir = learner.get_filename(dirpath, 
                    'repression_classifier', extra_dir)
        if force_choice: subdir = subdir + '_forced_choice'
        
        if not os.path.exists(subdir): os.makedirs(subdir)
        
            
        for replicate_id in ('', 1, 2, 3, 4):
            rep_str = get_rep_string(replicate_id)
            
            dataset = grouped
            targets = dataset.reset_index().filter(regex=r'.*_lfc')
            # Get rid of lfc columns    
            dataset = dataset.reset_index().filter(regex=r'(?!(.*_lfc|dex_over_kla.*|.*id|.*_tags))')
            # And then columns from other replicates
            dataset = dataset.reset_index().filter(regex=r'(({1}pu_1_kla)|{0})'.format('(?!(.*_\d_.*|.*_id))', 
                                                          rep_str and r'.*' + rep_str + r'.*|' or ''))
            print dataset.columns
            
            labels = targets['kla_{0}lfc'.format(rep_str)] <= -1
            
            print 'Total examples, positive: ', len(dataset), sum(labels)
            # Nulls should be zeroes. Fill those first.
            dataset = dataset.fillna(0)
            dataset = learner.make_numeric(dataset)
            dataset = learner.normalize_data(dataset)
            
            
            best_err = 1.0
            best_c = 0
            best_chosen = []
            possible_k = [20, 10, 5, 2]
            for k in possible_k:
                if force_choice:
                    chosen = ['kla_{0}bucket_score'.format(rep_str), 'dmso_{0}bucket_score'.format(rep_str)]
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

            
            
        