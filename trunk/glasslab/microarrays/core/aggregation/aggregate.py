'''
Created on Sep 1, 2010

@author: karmel

Most microarray analysis is not a simple comparison of two samples.

This module has classes and methods for comparing sets of data,
and for creating comprehensible representations for presentation
and review.
'''
from glasslab.microarrays.core.analyze import MicroarrayAnalyzer
from scipy.cluster.vq import vq, kmeans, whiten
import math
import numpy
from copy import copy
from glasslab.microarrays.core.aggregation.visualize import MicroarrayVisualizer
from glasslab.microarrays.core.aggregation.categorize import MicroarrayCategorizer



class MicroarrayAggregator(MicroarrayVisualizer, MicroarrayCategorizer):
    '''
    Special aggregator of MicroaarrayAnalyzers with methods to compile data
    that has been separated, averaged, and normalized. Compiled and normalized data
    can then be cross-compared and analyzed in the new context.
    
    This is  especially useful for multiple samples over a variety of time periods,
    such that after averaging and normalization for each time period, data can be
    reanalyzed in the context of the whole.
    
    .. warning:: 
    
        Each added data set must contain data for the same genes, in the same order.
     
    '''
    subset_analyzers = None
    ''' List of MicroarrayAnalyzers to be included in the aggregate. '''
    
    # For log transform differential analysis
    compared_samples = None
    differentials = None
    
    def __init__(self, subset_analyzers=None):
        self.subset_analyzers = subset_analyzers or []
        self.compared_samples, self.differentials = [],[]
        super(MicroarrayAggregator, self).__init__()

    def add_data_set(self, matrix, genes, samples, normalize=True):
        self.subset_analyzers.append(MicroarrayAnalyzer(matrix, genes, samples, normalize=normalize))
    
    def filter_rows(self):
        '''
        Convenience method; can be overwritten as necessary.
        '''
        return self.get_x_fold_genes(x=2)

    def sort_rows(self, genes, data_rows, selected_ids):
        '''
        Convenience method; can be overwritten as necessary.
        '''
        return genes, data_rows, selected_ids
    
    def _sort_rows_by_gene_functions(self, genes, data_rows, selected_ids):
        return self._sort_rows_by_gene_ontology(genes, data_rows, selected_ids, type='functions')

    def _sort_rows_by_gene_processes(self, genes, data_rows, selected_ids):
        return self._sort_rows_by_gene_ontology(genes, data_rows, selected_ids, type='processes')
    
    def _sort_rows_by_gene_ontology(self, genes, data_rows, selected_ids, type='functions'):
        '''
        Sort rows according to gene function or process. Not implemented by default.
        '''
        # First sort by annotation
        ontos = [(getattr(g, type),i) for i,g in enumerate(genes)]
        ontos.sort(reverse=True)
        # Pull out gene ids in the new order
        ontos, ordered_gene_indices = zip(*ontos)
        # Align the two lists we want to keep in order
        matrix = numpy.array([genes, data_rows, selected_ids])
        matrix_sorted = map(lambda row: [row[i] for i in ordered_gene_indices], matrix)
        # And reorder the rows of the numpy array
        #data_rows = numpy.array([data_rows[i] for i in ordered_gene_indices])
        return matrix_sorted[0], matrix_sorted[1], matrix_sorted[2]
        
    def get_x_fold_genes(self, x=2):
        ''' 
        Returns list of gene, log transform tuples for each sample
        when any sample has at least x-fold
        variation between control and test samples. 
        '''
        genes = []
        data_rows = []
        selected_ids = []
        # For each gene, extract log_val; if any log val is in range, store all
        for i in xrange(0, len(self.subset_analyzers[0].genes)):
            log_vals = []
            for analyzer in self.subset_analyzers:
                if analyzer.mean_log_transformations is None: 
                    analyzer.set_mean_log_transformations()
                log_vals.append(analyzer.mean_log_transformations[i])
            in_range = False
            for log_val in log_vals:
                if log_val < -math.log(x,2) or log_val > math.log(x,2): 
                    in_range = True
                    break
            if in_range: 
                genes.append(self.subset_analyzers[0].genes[i])
                data_rows.append(log_vals)
                selected_ids.append(i)
        return genes, numpy.array(data_rows), selected_ids
    
    def set_log_differentials(self):
        '''
        Sets differentials in log values for test samples
        that use the same control sample type.
        
        ::
        
            control_type: [indices of analyzers that use this type]
            
        Then, sets up matrices of differentials with relevant metadata.
        
        '''
        import itertools
        
        unique_controls = {}
        # First checks all subset analyzers and splits into sets:
        #     control_type: [indices of analyzers that use this type]
        for i,analyzer in enumerate(self.subset_analyzers):
            if analyzer.mean_log_transformations is None: 
                analyzer.set_mean_log_transformations()
            try: unique_controls[analyzer.control_samples[0].type].append(i)
            except: unique_controls[analyzer.control_samples[0].type] = [i]
        
        # Next, create lists of the relevant log differentials by index of samples
        compared_samples = []
        differentials = []
        for analyzers in unique_controls.values():
            if len(analyzers) <= 1: continue
            for first_i, second_i in itertools.combinations(analyzers, 2):
                first = self.subset_analyzers[first_i]
                second = self.subset_analyzers[second_i]
                compared_samples.append((first.test_samples[0],second.test_samples[0]))
                # One row of log transforms (one per gene) minus the other
                difference = numpy.array(first.mean_log_transformations) \
                            - numpy.array(second.mean_log_transformations)
                differentials.append(difference.tolist())
        differentials = numpy.transpose(numpy.array(differentials))
        self.compared_samples, self.differentials = compared_samples, differentials
    
    def _filter_rows_by_log_differential(self, differential=0.25, cols=None):
        '''
        Keep rows that have greater than 0.1 log differential
        between Kdo2 and MRL24+Kdo2
        '''
        if not self.differentials: self.set_log_differentials()
        genes = []
        data_rows = []
        selected_ids = []
        # For each gene, extract diff_val; if any diff_val is in range, store all
        for i,diff_values in enumerate(self.differentials):
            # Allow limiting of differential columns to just a set of indexed columns
            diff_vals = copy(diff_values)
            if cols: diff_vals = diff_vals[cols]
            # The math:
            # log2(x/control) - log2(y/control) = log2(x/y)
            # So, x/y = 2^.25 = ~119%
            # In other words, pick out rows at least ~19% different
            if abs(diff_vals).max() >= differential: 
                genes.append(self.subset_analyzers[0].genes[i])
                data_rows.append([a.mean_log_transformations[i] 
                                    for a in self.subset_analyzers])
                selected_ids.append(i)
        return genes, numpy.array(data_rows), selected_ids
    
    def _filter_for_specific_genes(self, gene_names=None, limiting_ids=None):
        '''
        A list of gene names is passed in. First, get list of relevant genes and ids by name, and id if necessary;
        then, from each subset analyzer, pull out the relevant data rows and merge with the others.
        '''
        if not gene_names: gene_names = []
        if not limiting_ids: limiting_ids = []
        selected = [(id,g) for id,g in enumerate(self.subset_analyzers[0].genes) 
                                                if g.gene_name in gene_names and id in limiting_ids]
        selected_ids, genes = zip(*selected)
        selected_ids = list(selected_ids) # Tuples can't be used for numpy indexing
        analyzer_data_rows = [numpy.array(a.mean_log_transformations)[selected_ids] 
                                                        for a in self.subset_analyzers]
        data_rows = numpy.transpose(numpy.array(analyzer_data_rows))
        return genes, data_rows, selected_ids

    def cluster_genes(self, cluster_count=10):
        ''' 
        Each gene is a vector, with measurements across samples as the points.
        Find clusters of genes that are co-expressed according to mean log transformation values.
        
        return -- list of 2D arrays.  Each array contains the data points that belong to a specific cluster.
        
        Uses kmeans algorithm to find the clusters. 
        '''
        # Get all genes with > 2-fold transformation to draw
        genes, data_rows, selected_ids = self.filter_rows()
        
        # @todo: dynamically choose cluster count based on distortion
        # Whiten the data to attain unit variance
        wh_data = whiten(data_rows)
        # Cluster the data, obtaining the code_book of clusters
        code_book,dist = kmeans(wh_data,cluster_count)
        # Obtain the cluster id for each row of data
        code_ids, distortion = vq(wh_data,code_book)
        # Group the original data by cluster
        clusters = []
        for i in xrange(len(code_book)):
            cluster = (numpy.compress(code_ids == i,genes,0),
                       numpy.compress(code_ids == i,data_rows,0),
                       numpy.compress(code_ids == i,selected_ids,0),
                       )
            clusters.append(cluster)
        return clusters
     

