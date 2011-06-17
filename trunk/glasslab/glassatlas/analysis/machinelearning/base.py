'''
Created on Jun 7, 2011

@author: karmel
'''
from __future__ import division
from glasslab.utils.parsing.delimited import DelimitedFileParser
import numpy
from scikits.learn.feature_selection.univariate_selection import SelectFpr,\
    f_classif
from matplotlib import pylab as pl
from mpl_toolkits.mplot3d import Axes3D # Necessary for matplotlib
from scikits.learn.cross_val import StratifiedKFold
from scikits.learn.metrics.metrics import roc_curve, auc, classification_report,\
    confusion_matrix, mean_square_error
import scipy
from glasslab.glassatlas.analysis.machinelearning.reduction import GlassPCA
import random

class BaseML(object):
    data = None # N x M matrix of N rows, M features, scaled
    raw_data = None 
    
    def __init__(self, data):
        self.raw_data = data
        self.data = numpy.float_(data)
        
    def scale_data(self):
        self.data -= self.data.mean(axis=0)
        self.data /= self.data.max(axis=0)
    
    def get_ml(self, probability=False):
        # Overwrite
        pass
    
    def order_features(self, draw=False, by_pval=False):
        x_indices = numpy.arange(self.data.shape[-1])
        
        ################################################################################
        # Univariate feature selection
        # As a scoring function, we use a F test for classification
        # We use the default selection function: the 10% most significant
        # features
        if by_pval:
            selector = SelectFpr(f_classif, alpha=0.1)
            selector.fit(self.data, self.labels)
            scores = -numpy.log10(map(lambda x: x or 10**-50, selector._pvalues))
            scores /= scores.max()
        else:
            self.classifier = self.get_ml(probability=True)
            self.classifier.fit(self.data, self.labels, class_weight='auto')
            scores = self.classifier.coef_[0]
            scores /= scores.max()
        
        # Compute correlation and scale score accordingly.
        # First, order scores
        # Return indices
        indices_set = list(enumerate(scores))
        indices_set.sort(key=lambda x: abs(x[1]), reverse=True)
        
        for index, score in indices_set[:int(len(indices_set)/2)]:
            for i, col in enumerate(self.data.T):
                if index == i: continue
                corr = abs(scipy.stats.pearsonr(self.data[:,index],col)[0])
                if  corr > .9:
                    # These are highly correlated; scale the lower-scored one
                    scores[i] = scores[i]*(1 - corr)
                    
        if draw:
            pl.figure(1)
            pl.clf()
        
            pl.bar(x_indices-.45, scores, width=.3,
                label=r'Univariate score ($-Log(p_{value})$)',
                color='g')
        
            ##########################################################
            # Compare to the weights of an SVM
            clf = self.get_ml()
            clf.fit(self.data, self.labels)
            
            svm_weights = (clf.coef_**2).sum(axis=0)
            svm_weights /= svm_weights.max()
            pl.bar(x_indices-.15, svm_weights, width=.3, label='SVM weight',
                    color='r')
            
            pl.title("Comparing feature selection")
            pl.xlabel('Feature number')
            pl.yticks(())
            pl.axis('tight')
            pl.legend(loc='upper right')
            pl.show()
        
        # Return indices
        indices_set = list(enumerate(scores))
        indices_set.sort(key=lambda x: abs(x[1]), reverse=True)
        ordered_indices = zip(*indices_set)[0]
        self.data = self.data[:,ordered_indices]
        return ordered_indices
    
class BaseClassifier(BaseML):
    labels = None # 1 x N list of binary labels (0,1)
    
    classifier = None
    folds = 3
    
    def __init__(self, data, labels):
        self.labels = numpy.array(map(int,labels))
        super(BaseClassifier, self).__init__(data)    
    
    def draw_roc(self, fields_used=None, label_field='', pca=False):
        # Classification and ROC analysis

        # Run classifier with crossvalidation and plot ROC curves
        cv = StratifiedKFold(self.labels, k=self.folds)
        self.classifier = self.get_ml(probability=True)
        
        mean_tpr = 0.0
        mean_fpr = numpy.linspace(0, 1, 100)
        
        for i, (train, test) in enumerate(cv):
            train_data = self.data[train]
            test_data = self.data[test]
            if pca:
                reducer = GlassPCA()
                reducer.get_pca(self.data[train])
                train_data, test_data = reducer.project_data(self.data[train], self.data[test])
            fitted = self.classifier.fit(train_data, self.labels[train], class_weight='auto')
            
            decisions = fitted.predict(test_data)
            print classification_report(self.labels[test], decisions)
            print confusion_matrix(self.labels[test], decisions)
            print mean_square_error(self.labels[test], decisions)
            
            if getattr(self.classifier, 'classes', None) is None or self.classifier.classes.shape[0] == 2:
                probas_ = fitted.predict_proba(test_data)
                # Compute ROC curve and area the curve    
                try: fpr, tpr, thresholds = roc_curve(self.labels[test], probas_[:,1])
                except IndexError: fpr, tpr, thresholds = roc_curve(self.labels[test], probas_)
                mean_tpr += scipy.interp(mean_fpr, fpr, tpr)
                mean_tpr[0] = 0.0
                roc_auc = auc(fpr, tpr)
                pl.plot(fpr, tpr, lw=1, label='ROC fold %d (area = %0.2f)' % (i, roc_auc))
            
        pl.plot([0, 1], [0, 1], '--', color=(0.6,0.6,0.6), label='Luck')
        
        mean_tpr /= len(cv)
        mean_tpr[-1] = 1.0
        mean_tpr = numpy.ma.fix_invalid(mean_tpr,fill_value=0)
        mean_auc = auc(mean_fpr, mean_tpr)
        pl.plot(mean_fpr, mean_tpr, 'k--',
                label='Mean ROC (area = %0.2f)' % mean_auc, lw=2)
        
        pl.xlim([-0.05,1.05])
        pl.ylim([-0.05,1.05])
        pl.xlabel('False Positive Rate')
        pl.ylabel('True Positive Rate')
        title = '%s ROC curve: %s' % (self.class_name, label_field)
        if fields_used: 
            annot_fields = ['%s (%.2f)' % (fields_used[i], self.classifier.coef_[0:,i]) for i in xrange(0,len(fields_used))]
            
            title += '\nUsing fields: ' + '\n'.join([', '.join(annot_fields[x:x+6]) for x in xrange(0,len(annot_fields),6)])
        pl.title(title, fontsize='small')
        pl.legend(loc="lower right")
        #pl.savefig('/Users/karmel/Desktop/pic_%d.png' % random.randint(0,99999))
        pl.show()
        
    def draw_xd(self, ax, indices, label_field='',dim=2):
        vals = list(set(self.labels))
        vals.sort()
        klasses = [numpy.array([row for i,row in enumerate(self.data) 
                             if self.labels[i] == val]) for val in vals]
        plot_args = {'linestyle':'None','markersize':7}
        
        markers = ['+','x','1','2']
        colors = ['red','blue','lime','orange']
        
        for i,klass in enumerate(klasses):
            ax.plot(*([klass[:,indices[x]] for x in xrange(0,dim)] + [markers[i]]), 
                    label='%s = %s (%d)' % (label_field, str(vals[i]), len(klass)),
                    color=colors[i],**plot_args)
        
        return ax
    
    def draw_2d(self, indices, features, label_field=''):
        fig = pl.figure()
        ax = fig.gca()
        ax = self.draw_xd(ax, indices, label_field=label_field, dim=2)
        
        ax.set_xlabel(features[0])
        ax.set_ylabel(features[1])
        ax.legend()
        #pl.savefig('/Users/karmel/Desktop/pic_%d.png' % random.randint(0,99999))
        pl.show()

    def draw_3d(self, indices, features, label_field=''):
        fig = pl.figure()
        ax = fig.gca(projection='3d')
        
        ax = self.draw_xd(ax, indices, label_field=label_field, dim=3)
        
        ax.set_xlabel(features[0])
        ax.set_ylabel(features[1])
        ax.set_zlabel(features[2])
        pl.legend()
        #pl.savefig('/Users/karmel/Desktop/pic_%d.png' % random.randint(0,99999))
        pl.show()

class BaseRegressor(BaseML):
    regressor = None
    targets = None
    
    def __init__(self, data, targets):
        self.targets = numpy.array(map(float,targets))
        super(BaseRegressor, self).__init__(data)
        
class MLSetup(object):
    text_data = None
    text_fields = None
    text_fields = 4 # How many fields are text, not useful here?
    
    def get_data_from_file(self, file_name=None, text_file_name=None, header=True):
        
        parser = DelimitedFileParser(file_name,header=header)
        data = parser.get_array()
        data = self.convert_to_float(data)
        fields = parser.fields
        
        if text_file_name:
            text_parser = DelimitedFileParser(text_file_name,header=header)
            text_data = text_parser.get_array()
            self.text_data = text_data
            self.text_fields = text_parser.fields
        else: self.text_data = []
        
        return data, fields
    
    def filter_data_no_infrastructure(self, data, fields):
        # Filter out rRNA, tRNA, etc.
        mask = data[:,fields.index('has_infrastructure')] == 0
        self.text_data = self.text_data[mask]
        return data[mask]
    
    def filter_data_dmso_upreg(self, data, fields):
        # Up-reg only
        mask = data[:,fields.index('dmso_kla_fc')] >= 1
        self.text_data = self.text_data[mask]
        return data[mask]
    
    def filter_data_refseq(self, data, fields):
        # Ref-seq only
        mask = data[:,fields.index('has_refseq')] == 1
        self.text_data = self.text_data[mask]
        return data[mask]
    
    def filter_data_has_change(self, data, fields):
        # For rows with fold-change features, filter out those with no 
        # significant change in any condition
        mask = numpy.array(map(lambda x: abs(x).max() >= .6, data))
        self.text_data = self.text_data[mask]
        return data[mask]
    
    def filter_data_score(self, data, fields, score=10):
        # Above passed score min
        mask = data[:,fields.index('transcript_score')] >= score
        self.text_data = self.text_data[mask]
        return data[mask]

    def convert_to_float(self, data):
        # Zero out pesky string columns so that we can convert to a float array;
        # Keeping the large array as strings causes memory alloc problems
        return numpy.float_(numpy.array([[0]*data.shape[0]]*self.text_fields + data[:,self.text_fields:].T.tolist())).T
        
    def get_selected_vectors(self, data, fields, selected):
        indices = [fields.index(s) for s in selected] 
        return self._get_vectors_and_indices(data, fields, indices) 
        
    def get_vectors_and_indices(self, data, fields):
        # Select columns
        indices = [fields.index('p65_score'), fields.index('cebpb_notx_score'), 
                   fields.index('pu_notx_score'), 
                   fields.index('p300_notx_score'),
                   fields.index('polii_notx_score'),
                   fields.index('ac_notx_score'),
                   fields.index('p65_avg_distance'),
                   fields.index('pu_notx_avg_distance'),
                   fields.index('p300_notx_avg_distance'),
                   fields.index('polii_notx_avg_distance'),
                   fields.index('ac_notx_avg_distance'),
                   
                   fields.index('pu_lps_score'),
                   fields.index('p300_lps_score'),
                   fields.index('polii_lps_score'),
                   fields.index('ac_kla_score'),
                   fields.index('cebpb_notx_avg_distance'),
                   fields.index('pu_lps_avg_distance'),
                   fields.index('p300_lps_avg_distance'),
                   fields.index('polii_lps_avg_distance'),
                   fields.index('ac_kla_avg_distance'),
                   
                   fields.index('me2_notx_score'),
                   fields.index('me2_kla_1h_score'),
                   fields.index('me2_kla_4h_score'),
                   fields.index('me2_kla_6h_score'),
                   fields.index('me2_kla_24h_score'),
                   fields.index('me2_kla_48h_score'),
                   fields.index('me2_dex_kla_score'),
                   fields.index('me2_notx_avg_distance'),
                   fields.index('me2_kla_1h_avg_distance'),
                   fields.index('me2_kla_4h_avg_distance'),
                   fields.index('me2_kla_6h_avg_distance'),
                   fields.index('me2_kla_24h_avg_distance'),
                   fields.index('me2_kla_48h_avg_distance'),
                   fields.index('me2_dex_kla_avg_distance'),
                   
                   fields.index('poliis2_notx_score'),
                   fields.index('poliis2_kla_score'),
                   fields.index('poliis2_dex_2h_score'),
                   fields.index('poliis2_dex_4h_score'),
                   fields.index('poliis2_dex_kla_score'),
                   fields.index('poliis2_notx_avg_distance'),
                   fields.index('poliis2_kla_avg_distance'),
                   fields.index('poliis2_dex_2h_avg_distance'),
                   fields.index('poliis2_dex_4h_avg_distance'),
                   fields.index('poliis2_dex_kla_avg_distance'),
                   
                   fields.index('notx_1h_tags'),
                   fields.index('strand'), fields.index('length'),
                   
                   fields.index('p65_upstream_score'), fields.index('cebpb_notx_upstream_score'), 
                   fields.index('pu_notx_upstream_score'), fields.index('pu_lps_upstream_score'),
                   fields.index('p300_notx_upstream_score'), fields.index('p300_lps_upstream_score'),
                   fields.index('polii_notx_upstream_score'), fields.index('polii_lps_upstream_score'),
                   fields.index('ac_notx_upstream_score'), fields.index('ac_kla_upstream_score'),
                   fields.index('p65_upstream_avg_distance'), fields.index('cebpb_notx_upstream_avg_distance'),
                   fields.index('pu_notx_upstream_avg_distance'), fields.index('pu_lps_upstream_avg_distance'),
                   fields.index('p300_notx_upstream_avg_distance'), fields.index('p300_lps_upstream_avg_distance'),
                   fields.index('polii_notx_upstream_avg_distance'), fields.index('polii_lps_upstream_avg_distance'),
                   fields.index('ac_notx_upstream_avg_distance'), fields.index('ac_kla_upstream_avg_distance'),
                   
                   fields.index('p65_downstream_score'), fields.index('cebpb_notx_downstream_score'), 
                   fields.index('pu_notx_downstream_score'), fields.index('pu_lps_downstream_score'),
                   fields.index('p300_notx_downstream_score'), fields.index('p300_lps_downstream_score'),
                   fields.index('polii_notx_downstream_score'), fields.index('polii_lps_downstream_score'),
                   fields.index('ac_notx_downstream_score'), fields.index('ac_kla_downstream_score'),
                   fields.index('p65_downstream_avg_distance'), fields.index('cebpb_notx_downstream_avg_distance'),
                   fields.index('pu_notx_downstream_avg_distance'), fields.index('pu_lps_downstream_avg_distance'),
                   fields.index('p300_notx_downstream_avg_distance'), fields.index('p300_lps_downstream_avg_distance'),
                   fields.index('polii_notx_downstream_avg_distance'), fields.index('polii_lps_downstream_avg_distance'),
                   fields.index('ac_notx_downstream_avg_distance'), fields.index('ac_kla_downstream_avg_distance'),
                   
                   fields.index('pu_score_change'),
                   fields.index('pu_score_ratio'),
                   fields.index('p300_score_change'),
                   fields.index('p300_score_ratio'),
                   fields.index('ac_score_change'),
                   fields.index('ac_score_ratio'),
                   
                   ]
        '''
                   fields.index('conservation_score'),
                   fields.index('has_refseq'), fields.index('has_erna'),
                   fields.index('line_count'), fields.index('sine_count'),
                   fields.index('simple_count'), fields.index('ltr_count'),
                   fields.index('dna_count'), fields.index('rrna_count'),
                   fields.index('trna_count'), fields.index('scrna_count'),
                   fields.index('srprna_count'), fields.index('satt_count'),
                   fields.index('line_length'), fields.index('sine_length'),
                   fields.index('simple_length'), fields.index('ltr_length'),
                   fields.index('dna_length'), fields.index('rrna_length'),
                   fields.index('trna_length'), fields.index('scrna_length'),
                   fields.index('srprna_length'), fields.index('satt_length'),
                   #fields.index('dex_4h_fc'),
#                   fields.index('mrl24_4h_fc'),
#                   fields.index('gw3965_4h_fc'),
#                   fields.index('qw0072_4h_fc'),
                   ]        
'''
        indices.sort()
        return self._get_vectors_and_indices(data, fields, indices)
        
    def _get_vectors_and_indices(self, data, fields, indices):
        # Remove fields that are invariant
        for i in indices[:]:
            if data[:,i].min() == data[:,i].max() == data[:,i].mean():
                indices.remove(i)
        
        feat_data = data[:,indices]
                
        return feat_data, indices