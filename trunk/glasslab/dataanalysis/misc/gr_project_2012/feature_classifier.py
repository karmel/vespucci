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
import math
from sklearn.metrics.metrics import confusion_matrix

if __name__ == '__main__':
    learner = LogisticClassifier()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/classification'
    dirpath = learner.get_path(dirpath)
    
    '''
    # First time file setup
    data = get_data_with_bucket_score(learner, dirpath)
    # Get mean of all values to compress
    grouped_prelim = data.groupby('glass_transcript_id',as_index=False)
    grouped = grouped_prelim.mean()
    # Except for tag_count which should be summed.
    grouped['tag_count'] = grouped_prelim['tag_count'].sum()['tag_count']
    
    grouped.to_csv(learner.get_filename(dirpath,'feature_vectors.txt'),sep='\t',index=False)
    
    raise Exception
    grouped = learner.import_file(learner.get_filename(dirpath, '../transcript_vectors.txt'))
    grouped = grouped.drop(['chr_name','ucsc_link_nod','gene_names',
                            'transcription_start','transcription_end'],axis=1)
    '''
    
    grouped = learner.import_file(learner.get_filename(dirpath, 'feature_vectors.txt'))
    
    if True:
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
                    extra_dir, 'pausing_ratio_{0}_{1}'.format(
                        str(min_ratio).replace('.','_'),str(min_diff).replace('.','_')))
        if force_choice: subdir = subdir + '_forced_choice'
        
        if not os.path.exists(subdir): os.makedirs(subdir)
        
            
        for replicate_id in ('', 1, 2, 3, 4):
            rep_str = get_rep_string(replicate_id)
            
            
            #grouped = grouped[grouped['kla_{0}lfc'.format(rep_str)] >= -.5]
            #grouped = grouped[grouped['score'] >= 100]
            pausing_states = grouped.filter(regex=r'(kla_dex_\d_bucket_score|kla_dex_bucket_score|' +\
                                            r'kla_\d_bucket_score|kla_bucket_score)')
            
            # First do some column cleanup..
            # Remove cols that are the kla_dex_bucket target; or that are not from the current replicate;
            # or that are id fields
            regex = r'(?!(kla_dex_\d_bucket_score|kla_dex_bucket_score|.*gene.*tags))' +\
                            r'(({1}pu_1_kla)|{0})'.format('(?!(.*_\d_.*|.*_id))', 
                                                          rep_str and r'.*' + rep_str + r'.*|' or '')
            dataset = grouped.filter(regex=regex)
        
            
            labels = pausing_states['kla_dex_{0}bucket_score'.format(rep_str)] \
                                /pausing_states['kla_{0}bucket_score'.format(rep_str)] >= min_ratio
            
            
            #For checking non-trivials,
            # where Dex+KLA start tags are not equal to KLA start tags
            # (since that would make the kla_dex_gene_body_lfc
            # perfectly predictive.
            mask = (grouped['kla_dex_{0}gene_start_tags'.format(rep_str)]\
                        /grouped['kla_{0}gene_start_tags'.format(rep_str)])
            mask = mask.fillna(0)
            mask = mask.apply(lambda x: bool(x and abs(math.log(x,2)) > .5))
            
            labels = map(lambda x: int(x[0] and x[1]), zip(labels, mask))
            
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
                    chosen = ['kla_{0}gene_body_lfc'.format(rep_str), 'dex_over_kla_{0}gene_body_lfc'.format(rep_str)]
                    
                else:
                    chosen = learner.get_best_features(dataset, labels, k=k)
                    
                num_features = len(chosen)
                
                err, c = learner.run_nested_cross_validation(dataset, labels, columns=chosen,
                            classifier_type='logistic',
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
            
            '''
            # Now check reliability on non-trivial examples,
            # where Dex+KLA start tags are not equal to KLA start tags
            # (since that would make the kla_dex_gene_body_lfc
            # perfectly predictive.
            mask = (grouped['kla_dex_{0}gene_start_tags'.format(rep_str)]\
                        /grouped['kla_{0}gene_start_tags'.format(rep_str)])
            mask = mask.fillna(0)
            mask = mask.apply(lambda x: bool(x and abs(math.log(x,2)) > .25))
            print sum(mask)
            
            test_vectors = dataset.ix[mask]
            test_labels = labels.ix[mask]
            print sum(test_labels)
            
            mod = learner.get_model(C=best_c)
            fitted = mod.fit(dataset[best_chosen],labels)
            predicted_probs = fitted.predict_proba(test_vectors)
            err = learner.mse(predicted_probs, test_labels.values)
            
            print confusion_matrix(test_labels.values, predicted_probs[:,1] > .5)
            
            print mod.coef_ 
            learner.draw_roc(label_sets=[(test_labels.values, predicted_probs)], 
                             save_path=learner.get_filename(subdir,'check_nontrivial_{0}group'.format(rep_str)))
            '''
    if False:
        # How about transrepression?
        try: force_choice = sys.argv[1].lower() == 'force'
        except IndexError: force_choice = False
        try: extra_dir = sys.argv[2]
        except IndexError: extra_dir = ''
        
        subdir = learner.get_filename(dirpath, 
                    'transrepression' + extra_dir)
        if force_choice: subdir = subdir + '_forced_choice'
        
        if not os.path.exists(subdir): os.makedirs(subdir)
        
            
        for replicate_id in ('', 1, 2, 3, 4):
            rep_str = get_rep_string(replicate_id)
            
            dataset = grouped
            dataset['{0}pausing_ratio'.format(rep_str)] = dataset['kla_dex_{0}bucket_score'.format(rep_str)] \
                                                            /dataset['kla_{0}bucket_score'.format(rep_str)]
            targets = dataset.reset_index().filter(regex=r'.*_lfc')    
            dataset = dataset.reset_index().filter(regex=r'(?!(.*_lfc|kla_dex.*|dex_over_kla.*|.*id))')
            
            
            labels = targets['dex_over_kla_{0}gene_body_lfc'.format(rep_str)] <= -.58
            #labels_2 = targets['dex_over_kla_{0}lfc'.format(rep_str)] <= -.58
            
            #labels = map(lambda x: int(x[0] and x[1]), zip(labels, labels_2))
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
                    chosen = ['gr_kla_dex_tag_count', '{0}pausing_ratio'.format(rep_str)]
                    #chosen = ['kla_{0}bucket_score'.format(rep_str), 'tag_count']
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

            
            
        