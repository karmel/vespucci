'''
Created on Apr 14, 2012

@author: karmel, martin
'''
from __future__ import division
import datetime
import numpy
from sklearn.metrics.metrics import roc_curve, auc
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer

class Learner(TranscriptAnalyzer):
    
    def get_year(self, x):
        try: return int(x)//100
        except ValueError: return x
    
    def get_month(self, x):
        try: return int(x) % 100
        except ValueError: return x
    
    def get_timedelta(self, x):
        try: 
            delta = datetime.date.today() - datetime.date(int(x)//100,int(x) % 100,1)
            return delta.days
        except ValueError: return x
        
    def get_char(self, x, i):
        try: return str(x)[i]
        except IndexError: return ''
    
    def get_bool(self, x):
        try: return int(int(x) > 0)
        except ValueError: return x
        
    def get_region(self, x):
        return x[:2]
    
    def get_quantile(self, x, col=None, k=4, boundaries=None):
        try: int(x)
        except ValueError: return x
        if not boundaries: 
            boundaries = self.get_quantile_boundary(k, col)
        for i, b in enumerate(boundaries):
            if x <= b: return i
        return k
    
    def get_quantile_boundary(self, k, col):
        return [col.quantile(i*1/k) for i in xrange(1,k)] 
    
    def make_numeric(self, data):
        '''
        Turn string or category columns into numbers.
        '''
        print 'Making data numerical...'
        
        for col in data.columns:
            vals = list(set(data[col].dropna()))
            vals.sort()
            
            categorical = False
            def get_val(x):
                try: 
                    x[:2]
                    categorical = True
                    # We're a string; convert to int.
                    try: 
                        if not categorical and float(x) == float(str(float(x))):
                            return float(x)
                        else: raise ValueError # We don't want to convert codes like 00 to ints
                    except (ValueError, IndexError):
                        # If can't be converted directly, get category index  
                        try: return vals.index(x)
                        except ValueError: return None
                except TypeError:
                    # We're an int or float; leave as is.
                    return x
                
            
            data[col] = data[col].map(get_val)
        
        return data
    
    def normalize_data(self, data):
        '''
        All fields reduced to range [-1, 1].
        '''
        print 'Normalizing data...'
        
        # First remove all cols with std = 0, since we don't care about those.
        data = data[data.columns[data.std(axis=0) > 0]]
        
        # Recenter with mean 0, std 1
        data = (data - data.mean(axis=0))/data.std(axis=0)
        return data
    
    def sample_std(self, vals):
        '''
        Calc std, adjusting for number of observations
        '''
        sample_mean = numpy.mean(vals)
        n = len(vals)
        return (sum((sample_mean - x)**2 for x in vals)/n)**.5

    def get_auc(self, labels_true, labels_prob):
        fpr, tpr, _ = roc_curve(labels_true, labels_prob)
        return auc(fpr, tpr)

    def mse(self, predicted, true):
        try: d = predicted - true
        except ValueError:
            # Working with a scikits probabilities array
            d = predicted[:,1] - true
        return numpy.inner(d,d)/len(d)
