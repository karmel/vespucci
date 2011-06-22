'''
Created on Jun 7, 2011

@author: karmel
'''
from __future__ import division
from glasslab.glassatlas.analysis.machinelearning.base import BaseClassifier, MLSetup
from scikits.learn.linear_model.stochastic_gradient import SGDClassifier
import numpy
import random

class GlassSGDClassifier(BaseClassifier):
    class_name = 'SGD'
    
    def get_ml(self, **kwargs):
        n_iter = int(10**6/self.data.shape[0]/self.folds)
        return SGDClassifier(loss='log', n_iter=n_iter, shuffle=True)
    

if __name__ == '__main__':
    setup = MLSetup()
    data, fields = setup.get_data_from_file(file_name='/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Classification of fold change/feature_vectors_6.txt',header=True)
    #data, fields = setup.get_data_from_file(file_name='/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Classification of fold change/erna/erna_vectors_3.txt',header=True)
    
    #data = setup.filter_data_no_infrastructure(data,fields)
    #data = setup.filter_data_dmso_upreg(data,fields)
    #data = setup.filter_data_refseq(data,fields)
    #data = setup.filter_data_score(data,fields)
    #data = numpy.array(filter(lambda x: abs(float(x[fields.index('length')])) >= 2000, data))
    #data = numpy.array(filter(lambda x: abs(float(x[fields.index('dmso_4h_tags')])) >= 20000, data))
    
    # Select columns
    feat_data, indices = setup.get_vectors_and_indices(data, fields, erna=False)
    label_field = 'kla_1h_fc'
    labels = map(lambda x: int(x >= 1), data[:,fields.index(label_field)].tolist())
    #labels = map(lambda x: int(x <= -1 and -1) or (x >= 1 and 1) or 0), data[:,fields.index(label_field)].tolist())
    #labels = map(lambda x: .55*numpy.random.randn(), data[:,fields.index(label_field)].tolist())
    
    classifier = GlassSGDClassifier(feat_data,labels)
    classifier.scale_data()
    
    ordered_indices = classifier.order_features(by_pval=True)
    optimal_count = 20#classifier.determine_feature_count()
    
    indices_to_use = ordered_indices[:optimal_count]#min(optimal_count,10)]
    indices = [indices[x] for x in indices_to_use]
    fields_used = [fields[x] for x in indices]
    print 'Using fields: %s' % str(fields_used)
    
    orig_data = classifier.data[:]
    classifier.data = classifier.data[:,0:optimal_count]
    classifier.draw_roc(fields_used=fields_used,label_field=label_field, pca=False)
    #classifier.draw_roc(fields_used='',label_field=label_field, pca=True)
    classifier.data = orig_data
    '''
    feature_set = ['polii_lps_score', 'ac_notx_score', 'ac_kla_score',]
    
    classifier.draw_2d([indices.index(fields.index(feat)) for feat in feature_set], feature_set, label_field=label_field)
    classifier.draw_3d([indices.index(fields.index(feat)) for feat in feature_set], feature_set, label_field=label_field)
    '''