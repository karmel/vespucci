'''
Created on Jun 10, 2011

@author: karmel
'''
from time import time
from scikits.learn.decomposition.pca import RandomizedPCA
class GlassPCA(object):
    '''
    Reduce dimensionality of passed data set to speed up any subsequent
    classification or regression.
    '''
    pca = None
    number = 2
    def get_pca(self, train):
        print "Extracting the top %d components from %d rows" % (
            self.number, train.shape[0])
        t0 = time()
        pca = RandomizedPCA(n_components=self.number, whiten=True).fit(train)
        print "Done in %0.3fs" % (time() - t0)
        
        self.pca = pca
        return pca
    
    def project_data(self, train, test):        
        print "Projecting the input data on the principal components' orthonormal basis"
        t0 = time()
        train_pca = self.pca.transform(train)
        test_pca = self.pca.transform(test)
        print "Done in %0.3fs" % (time() - t0)

        return train_pca, test_pca