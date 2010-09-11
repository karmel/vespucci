'''
Created on Jul 27, 2010

@author: karmel

The basic formulas used for normalization, transformation, and so on of data
are derived from:

Microarray data normalization and transformation
John Quackenbush
nature genetics supplement | volume 32 | december 2002
(Available at http://www.cs.cmu.edu/~zivbj/class05/reading/norm.pdf)

'''
from __future__ import division
import numpy
from scipy.cluster.vq import vq, kmeans, whiten
from copy import copy
import math

class MicroarrayAnalyzer(object):
    '''
    Data object used for managing, storing, and analyzing microarray data.
    Includes methods for manipulating, normalizing, and separating data
    such that useful analysis is possible.
    '''
    matrix = None
    genes = None
    samples = None
    
    test_samples = None
    test_matrix = None
    control_samples = None
    control_matrix = None
    
    normalize = True
    
    original_matrix = None
    expression_ratios = None
    normalization_factors = None
    log_transformations = None
    mean_log_transformations = None
    z_scores = None
    
    def __init__(self, matrix, genes, samples, normalize=None):
        super(MicroarrayAnalyzer, self).__init__()
        if matrix.shape[0] != len(genes):
            raise MicroarrayDataError('Please ensure you have the correct number of genes specified.')
        if matrix.shape[1] != len(samples):
            raise MicroarrayDataError('Please ensure you have the correct number of samples specified.')
        
        self.matrix, self.genes, self.samples = matrix, genes, samples
        # Keep a copy of the original data for introspection
        self.original_matrix = copy(self.matrix)
        
        if normalize is not None: self.normalize = normalize
        
    def split_samples(self):
        ''' 
        Split samples into two groups-- control and test. 
        
        Sets two lists of sample records-- control and test,
        and two separate matrices of values, with each column separated depending on 
        whether or not it is a control. 
        '''
        self.control_samples = [sample for sample in self.samples if sample.control]
        self.test_samples = [sample for sample in self.samples if not sample.control]
        control_matrix = [self.matrix[:,i] for i,sample 
                          in enumerate(self.samples) if sample.control]
        test_matrix = [self.matrix[:,i] for i,sample 
                       in enumerate(self.samples) if not sample.control]
        
        # Sometimes we have fewer controls than samples; reuse the controls for comparison
        if len(test_matrix) > len(control_matrix):
            existing_samples = len(control_matrix)
            for missing_i in xrange(0,len(test_matrix) - existing_samples):
                # Loop through the existing control samples, reusing each
                # in order until all test samples are paired
                control_matrix.append(control_matrix[missing_i % existing_samples])
        self.control_matrix = numpy.transpose(numpy.array(control_matrix))
        self.test_matrix = numpy.transpose(numpy.array(test_matrix))
    
    ##########################################################
    # Data derivation methods
    ##########################################################
    def set_expression_ratios(self):
        ''' 
        Set an matrix of expression ratios.
        
        This assumes there are pairs of two samples with data across all genes, and that
        one sample has been marked as the control sample.
        
        For m genes and n pairs of samples, an n x m matrix is created, with each gene's expression ratio
        calculated and stored. The expression ratio is defined as::
        
            T = test_sample_expression/control_sample_expression
            
        ''' 
        
        if self.test_matrix is None: self.split_samples()
        expression_ratios = []
        for i,test_col in enumerate(numpy.transpose(self.test_matrix)):
            control_col = self.control_matrix[:,i]
            sample_ratios = [test_val/control_col[k] for k,test_val in enumerate(test_col)]
            expression_ratios.append(sample_ratios)
        self.expression_ratios = numpy.transpose(numpy.array(expression_ratios))
        
    def set_total_intensity_normalization_factors(self):
        ''' 
        In order to normalize across samples, we assume that the total amount
        of RNA in each sample of each test/control pair is equal.
        
        To normalize the expression ratios, then, we calculate a normalization factor::
        
            N = sum(expression level for each gene in test)/sum(expression level for each gene in control)
        
        The normalization factor, then, is set and stored for each test/control pair.
        
        If normalize = False, normalization is skipped, and a 1:1 ratio is assumed. 
        '''
        if self.test_matrix is None: self.split_samples()
            
        if not self.normalize:
            self.normalization_factors = [1]*len(self.test_samples)
        else:
            norm_factors = []
            for i,test_col in enumerate(numpy.transpose(self.test_matrix)):
                norm_factors.append(sum(test_col)/sum(self.control_matrix[:,i]))
            self.normalization_factors = norm_factors
    
    def set_log_transformations(self):
        ''' 
        Set the log base 2 transformations of expression ratios to determine
        relative up- and down-regulation for each gene.
        
        For m genes and n test/control sample pairs, a n x m matrix is created, 
        with each gene's log transformation calculated and stored. The log transformation is defined as::
        
            T = log2(expression_ratio) - log2(normalization_factor) 
            
        '''
        if self.expression_ratios is None: self.set_expression_ratios()
        if self.normalization_factors is None: self.set_total_intensity_normalization_factors()
        log_transformations = []
        for i,ratio_col in enumerate(numpy.transpose(self.expression_ratios)):
            col_transformations = [(math.log(ratio,2) - math.log(self.normalization_factors[i],2))
                                   for ratio in ratio_col]
            log_transformations.append(col_transformations)
        self.log_transformations = numpy.transpose(numpy.array(log_transformations))
        
    def set_mean_log_transformations(self):
        ''' 
        For n replicate pairs of test/control samples, the mean log transformation
        is defined as::
            
            log2(mean_T_for_gene_j) = (1/number of pairs)*
                                (log2(product of each sample pair's log transform for gene j)
                                - log2(product of each sample pair's norm factor for gene j))

        This can be simplified and manipulated in a number of ways,
        but, given that we store each log_transformation separately for conceptual demonstration,
        the simplest mean calculation is to add and subsequently divide. 
        '''
        if not self.log_transformations: self.set_log_transformations()
        mean_transformations = []
        for logs_per_gene in self.log_transformations:
            mean_transformations.append(sum(logs_per_gene)/len(logs_per_gene))
        self.mean_log_transformations = mean_transformations
            
    def set_z_scores(self):
        ''' 
        An alternate to fold-analysis for determining differential expression
        is an intensity-aware z-score comparing mean log transform and the standard
        deviation of the log transform values for a given sample pair. 
        '''
        if self.mean_log_transformations is None: self.set_mean_log_transformations()
        z_scores = []
        #std_dev = numpy.std(self.mean_log_transformations)
        for i,log_val in enumerate(self.mean_log_transformations): 
            z_scores.append(log_val/numpy.std(self.log_transformations[i]))
        self.z_scores = z_scores
        
    def get_x_fold_genes(self, x=2):
        ''' 
        Returns list of genes, log transform tuples with x-fold
        variation between control and test samples. 
        '''
        if self.mean_log_transformations is None: self.set_mean_log_transformations()
        genes = []
        for i, log_val in enumerate(self.mean_log_transformations):
            if log_val < -math.log(x,2) or log_val > math.log(x,2): 
                genes.append((self.genes[i], log_val))
        return genes
        
    def get_differential_genes_by_z_score(self, deviations=1.96):
        ''' 
        Returns a list of genes at least [deviations] standard deviations
        away from the mean. 
        '''
        if self.z_scores is None: self.set_z_scores()
        genes = []
        for i, z_score in enumerate(self.z_scores):
            if numpy.abs(z_score) > deviations: 
                genes.append((self.genes[i], z_score))
        return genes
    
    ##########################################################
    # Clustering and grouping methods
    ##########################################################
    def cluster_genes(self, cluster_count=None):
        ''' 
        Each gene is a vector, with measurements across samples as the points.
        Find clusters of genes that are co-expressed.
        ''' 
        return self.cluster(self.matrix, self.genes, cluster_count)
        
    def cluster_samples(self, cluster_count=None):
        ''' 
        Each sample is a vector, with measurements across genes as the points.
        Find clusters of samples that behave similarly for genes.
        ''' 
        return self.cluster(numpy.transpose(self.matrix), self.samples, cluster_count)
        
    def cluster(self, matrix, reference_array, cluster_count):
        ''' 
        For the given matrix and returnable reference array, cluster passed data rows.
        
        return -- list of 2D arrays.  Each array contains the data points that belong to a specific cluster.
        
        Uses kmeans algorithm to find the clusters. 
        '''
        # @todo: dynamically choose cluster count based on distortion
        # Whiten the data to attain unit variance
        wh_data = whiten(matrix)
        # Cluster the data, obtaining the code_book of clusters
        code_book,dist = kmeans(wh_data,cluster_count)
        # Obtain the cluster id for each row of data
        code_ids, distortion = vq(wh_data,code_book)
        # Group the original data by cluster
        clusters = []
        for i in xrange(len(code_book)):
            cluster = numpy.compress(code_ids == i,reference_array,0)
            clusters.append(cluster)
        return clusters

class MicroarrayDataError(Exception): pass