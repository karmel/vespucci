'''
Created on Jun 2, 2011

@author: karmel
'''
from __future__ import division
import numpy
from scikits.learn import svm
from scikits.learn.feature_selection import RFECV
from scikits.learn.metrics import zero_one
from scikits.learn.cross_val import StratifiedKFold
from matplotlib import pylab as pl
from glasslab.glassatlas.analysis.machinelearning.base import BaseClassifier, MLSetup

class GlassSVMClassifier(BaseClassifier):
    class_name = 'SVM'
    kernel = 'linear'
    
    def get_ml(self, probability=False):
        return svm.SVC(kernel=self.kernel, probability=probability)
        
    def determine_feature_count(self, draw=False):
        svc = svm.SVC(kernel=self.kernel)
        rfecv = RFECV(estimator=svc, n_features=2, percentage=0.1, loss_func=zero_one)
        rfecv.fit(self.data, self.labels, cv=StratifiedKFold(self.labels, 2))
        
        optimal_number = rfecv.support_.sum()
        
        print 'Optimal number of features: %d' % optimal_number
        
        if draw:
            pl.figure()
            pl.semilogx(rfecv.n_features_, rfecv.cv_scores_)
            pl.xlabel('Number of features selected')
            pl.ylabel('Cross validation score (nb of misclassifications)')
            # 15 ticks regularly-space in log
            x_ticks = numpy.unique(numpy.logspace(numpy.log10(2),
                                            numpy.log10(rfecv.n_features_.max()),
                                            15,
                                ).astype(numpy.int))
            pl.xticks(x_ticks, x_ticks)
            pl.show()
        
        return optimal_number
    
    
        
if __name__ == '__main__':
    setup = MLSetup()
    data, fields = setup.get_data_from_file(file_name='/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Classification of fold change/feature_vectors_7.txt',header=True)
    #data, fields = setup.get_data_from_file(file_name='/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Classification of fold change/erna/erna_vectors_3.txt',header=True)
    
    #data = setup.filter_data_no_infrastructure(data,fields)
    #data = setup.filter_data_dmso_upreg(data,fields)
    #data = setup.filter_data_refseq(data,fields)
    #data = numpy.array(filter(lambda x: abs(float(x[fields.index('dmso_kla_fc')])) <= 1, data))
    
    # Select columns
    feat_data, indices = setup.get_vectors_and_indices(data, fields, erna=False)
    label_field = 'kla_1h_fc'
    labels = map(lambda x: int(x <= -1), data[:,fields.index(label_field)].tolist())
    #labels = map(lambda x: int(x), data[:,fields.index(label_field)].tolist())
    
    classifier = GlassSVMClassifier(feat_data,labels)
    classifier.scale_data()
    
    ordered_indices = classifier.order_features(by_pval=False)
    optimal_count = 10#classifier.determine_feature_count()
    
    indices_to_use = ordered_indices[:optimal_count]#min(optimal_count,10)]
    indices = [indices[x] for x in indices_to_use]
    fields_used = [fields[x] for x in indices]
    print 'Using fields: %s' % str(fields_used)
    
    orig_data = classifier.data[:]
    classifier.data = classifier.data[:,0:optimal_count]
    classifier.draw_roc(fields_used=fields_used,label_field=label_field)
    classifier.data = orig_data
    '''
    feature_set = ['polii_lps_score', 'has_refseq', 'p300_notx_score', ]
    classifier.draw_2d([indices.index(fields.index(feat)) for feat in feature_set], feature_set, label_field=label_field)
    classifier.draw_3d([indices.index(fields.index(feat)) for feat in feature_set], feature_set, label_field=label_field)
    '''