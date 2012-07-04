'''
Created on May 12, 2012

@author: martin, karmel
'''
from __future__ import division
from random import shuffle
from sklearn.feature_selection.univariate_selection import SelectKBest,\
    f_classif
from sklearn.cross_validation import StratifiedKFold
from sklearn import linear_model
from sklearn.metrics.metrics import roc_curve, auc
from pandas import Series
from glasslab.dataanalysis.machinelearning.base import Learner
from matplotlib import pyplot

class LogisticClassifier(Learner):
    
    Cs = [10**C for C in range(-3,3)]
    def get_best_features(self, data, labels, k=3):
        '''
        Using the scikit-learn library, narrow down feature set.
        '''
        num_feat = len(data.columns)
        while num_feat > k:
            num_feat = max(k, num_feat//2)
            selector = SelectKBest(f_classif, k=num_feat)
            selector.fit(data, labels)
        
            chosen = selector.get_support()
            if sum(selector._pvalues[chosen]) > 0:
                data = data[data.columns[chosen]]
            else: 
                # Many of our p-vals are zero. Accept all.
                data = data[data.columns[selector._pvalues == 0]]
                num_feat = k
        
        print data.columns 
        return data.columns

    def get_k_features(self, data, labels, k=None):
        all_feat = range(len(data.columns))
        if k is None: return all_feat
        return all_feat[:k]

    def run_nested_cross_validation(self, data, labels, k=3, Cs=None, 
                                    error_f=None, lower_is_better=True,
                                    columns=None, balance=False,
                                    draw_roc=False):
        '''
        Run nested CV on data with passed k folds.
        
        If columns is passed, it should be a list of columns to subset from data.
        Otherwise, all of data is used.
        
        Data is assumed to be a pandas dataframe or similar.
        Cs can also be passed as a list of C parameter values to use.
        
        Error_f is a function for measuring error that takes predicted probabilities
        and true labels. Defaults to MSE.
        
        Uses the scikit-learn LogisticRegression library.
        '''
        if columns: data_chosen = data[columns]
        Cs = Cs or self.Cs
        error_f = error_f or self.mse
        
        best_c = 0
        
        try: cv_outer = StratifiedKFold(labels.values, k=k)
        except AttributeError:
            # Labels needs to be a pandas series
            labels = Series(labels)
            cv_outer = StratifiedKFold(labels.values, k=k)
        
        outer_metric, for_roc = [], []
        for train_outer, test_outer in cv_outer:
            mod = linear_model.LogisticRegression(C=1.0, penalty='l1', tol=1e-6)
            c_metric = []
            for c in Cs:
                cv_inner = StratifiedKFold(labels.ix[train_outer].values, k=k)
                mod.set_params(C=c)
                inner_metric = []
                for train_inner, test_inner in cv_inner:
                    # Balance rare classes if necessary:
                    if balance:
                        data_balanced, labels_balanced = self.balance_classes(
                            data_chosen.ix[train_inner], labels.ix[train_inner])
                    else: 
                        data_balanced, labels_balanced = data_chosen.ix[train_inner], labels.ix[train_inner] 
                    
                    fitted = mod.fit(data_balanced, labels_balanced)
                    
                    # Predict probabilities
                    predicted_probs = fitted.predict_proba(data_chosen.ix[test_inner])
                    
                    
                    err = error_f(predicted_probs, labels.ix[test_inner].values)
                    inner_metric.append(err)
                error_for_this_c = sum(inner_metric)/len(inner_metric)
                print "Average Error: ", error_for_this_c, ", for C: ", c
                c_metric.append(error_for_this_c)
            
            best_c = self.get_best_c(Cs, c_metric, lower_is_better=lower_is_better)
            
            # Now that we have selected the best parameter, apply to outer set.
            mod.set_params(C=best_c)
            fitted = mod.fit(data_chosen.ix[train_outer], labels.ix[train_outer])
            
            predicted_probs = fitted.predict_proba(data_chosen.ix[test_outer])
            err = error_f(predicted_probs, labels.ix[test_outer].values)
            
            for_roc.append((labels[test_outer].values, predicted_probs))
            
            outer_metric.append(err)

        mean_metric = sum(outer_metric)/len(outer_metric)

        print "Mean Nested CV Error for best c: ", mean_metric, ", C: ", best_c
        
        return mean_metric, best_c, for_roc

    def get_best_c(self, Cs, metric, lower_is_better=True):
        paired = zip(metric, Cs)
        paired.sort(reverse=lower_is_better)
        return paired[0][1]
    
    def balance_classes(self, data, labels):
        pos = data[labels == True]
        neg = data[labels == False]
        
        indices = neg.index.values
        shuffle(indices)
        indices = indices[:(len(neg) - len(pos))]
        data = data.drop(indices, axis=0)
        labels = labels.drop(indices, axis=0)
        return data, labels
        
    def draw_roc(self, label_sets, title='', save_path='', show_plot=True):
        # Compute ROC curve and area the curve
        pyplot.clf()
            
        for i, (labels, probas) in enumerate(label_sets):
            fpr, tpr, _ = roc_curve(labels, probas[:, 1])
            roc_auc = auc(fpr, tpr)
            
            # Plot ROC curve
            pyplot.plot(fpr, tpr, label='Training fold {0} (area = {1})'.format(i+1, round(roc_auc,2)))
        
        pyplot.plot([0, 1], [0, 1], 'k--')
        pyplot.xlim([0.0, 1.0])
        pyplot.ylim([0.0, 1.0])
        pyplot.xlabel('False Positive Rate')
        pyplot.ylabel('True Positive Rate')
        pyplot.title(title)
        pyplot.legend(loc="lower right")
        pyplot.savefig(save_path)
        if show_plot: pyplot.show()
        
        