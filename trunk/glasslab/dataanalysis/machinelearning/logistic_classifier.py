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
from sklearn.metrics.metrics import roc_curve, auc, confusion_matrix
from pandas import Series
from glasslab.dataanalysis.machinelearning.base import Learner
from matplotlib import pyplot
import numpy
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.cm import register_cmap, get_cmap

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
        
        return data.columns

    def get_k_features(self, data, labels, k=None):
        all_feat = range(len(data.columns))
        if k is None: return all_feat
        return all_feat[:k]

    def run_nested_cross_validation(self, data, labels, k=3, columns=None, 
                                    draw_roc=True, draw_decision_boundaries=True,
                                    title_suffix='', save_path_prefix='',
                                    balance=True, Cs=None, error_f=None, higher_is_better=False,
                                    threshold_p=.5):
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
        if columns is not None: data_chosen = data[columns]
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
            
            best_c = self.get_best_c(Cs, c_metric, higher_is_better=higher_is_better)
            
            # Now that we have selected the best parameter, apply to outer set.
            mod.set_params(C=best_c)
            
            # Balance rare classes if necessary:
            if balance:
                data_balanced, labels_balanced = self.balance_classes(
                    data_chosen.ix[train_outer], labels.ix[train_outer])
            else: 
                data_balanced, labels_balanced = data_chosen.ix[train_outer], labels.ix[train_outer] 
            
            predicted_probs = fitted.predict_proba(data_chosen.ix[test_outer])
            err = error_f(predicted_probs, labels.ix[test_outer].values)
            
            print confusion_matrix(labels[test_outer].values, predicted_probs[:,1] > threshold_p)
            
            for_roc.append((labels[test_outer].values, predicted_probs))
            
            outer_metric.append(err)

        mean_metric = sum(outer_metric)/len(outer_metric)

        print 'Mean Nested CV Error for best c: ', mean_metric, ', C: ', best_c
        print 'Final intercept: ', fitted.intercept_[0]
        print 'Final columns, coefficients: '
        print zip(columns, fitted.coef_[0])
        
        if draw_decision_boundaries:
            self.draw_decision_boundaries(mod, data_chosen.columns, 
                                          data_chosen.ix[train_outer].as_matrix(), 
                                          labels.ix[train_outer].values,
                                          title = 'Decision Boundaries: ' + title_suffix, 
                                          save_path = save_path_prefix + '_decision_boundaries.png'
                                          )
            
        if draw_roc:
            self.draw_roc(for_roc, 
                          title = 'ROC for {1} features, c = {2}: {0}'.format(
                                title_suffix, len(data_chosen.columns), best_c), 
                          save_path = save_path_prefix + '_roc.png')
        return mean_metric, best_c

    def get_best_c(self, Cs, metric, higher_is_better=False):
        paired = zip(metric, Cs)
        paired.sort(reverse=higher_is_better)
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
        
    def draw_roc(self, label_sets, title='', save_path='', show_plot=False):
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
        
    def draw_decision_boundaries(self, model, columns, training_data, training_labels,
                                 title='', save_path='', show_plot=False):
        '''
        From
        http://scikit-learn.org/stable/auto_examples/linear_model/plot_iris_logistic.html#example-linear-model-plot-iris-logistic-py
        '''
        h = .02  # step size in the mesh
        
        # Plot the decision boundary. For that, we will asign a color to each
        # point in the mesh [x_min, m_max]x[y_min, y_max].
        # Note that we're only taking the first two features here.
        x_min, x_max = training_data[:, 0].min() - .5, training_data[:, 0].max() + .5
        y_min, y_max = training_data[:, 1].min() - .5, training_data[:, 1].max() + .5
        xx, yy = numpy.meshgrid(numpy.arange(x_min, x_max, h), numpy.arange(y_min, y_max, h))
        Z = model.predict(numpy.c_[xx.ravel(), yy.ravel()])
        
        # WHY ARE ALL MATPLOTLIB COLORMAPS UGLY?
        two_tone_cmap = LinearSegmentedColormap.from_list('two_tone_cmap',['#C9D9FB','#915EAB'])
        register_cmap(cmap=two_tone_cmap)
        cmap_instance = get_cmap('two_tone_cmap')
        # Put the result into a color plot
        Z = Z.reshape(xx.shape)
        pyplot.figure()
        pyplot.pcolormesh(xx, yy, Z, cmap=cmap_instance, alpha=.8)
        
        # Plot also the training points
        pyplot.scatter(training_data[:, 0], training_data[:, 1], 
                       linewidths=.6,
                       c=training_labels, edgecolors='k', cmap=cmap_instance)
        pyplot.xlabel('Normalized {0}'.format(columns[0]))
        pyplot.ylabel('Normalized {0}'.format(columns[1]))
        
        pyplot.xlim(xx.min(), xx.max())
        pyplot.ylim(yy.min(), yy.max())
        pyplot.title(title)
        
        pyplot.savefig(save_path)
        if show_plot: pyplot.show()