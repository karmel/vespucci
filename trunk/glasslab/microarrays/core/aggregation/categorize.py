'''
Created on Sep 10, 2010

@author: karmel
'''
from __future__ import division
from glasslab.utils.geneannotation.geneontology import GOAccessor
import numpy
from scipy.stats import binom_test
 
class MicroarrayCategorizer(object):
    '''
    Methods for calculating statistics over and categorizing MicroarrayAggregator
    results.
    
    .. warning::
    
        This is not a standalone object. This is intended to be a
        partial interface, implemented by the aggregator,
        separated for ease of code use.
    
    '''
    max_p_val = .05
    background_ontologies = None
    background_term_count = None
    foreground_ontologies = None
    foreground_term_count = None
    
    go_accessor = None
    
    def set_background_ontology(self):
        '''
        For the total set of genes being looked at in this aggregator,
        get ontological terms from the GeneOntology database.
        '''
        if not self.go_accessor: self.go_accessor = GOAccessor()
        
        gene_names = [g.gene_name for g in self.subset_analyzers[0].genes]
        self.background_ontologies = self.go_accessor.get_ancestors_for_genes(gene_names)
        results_array = numpy.array(self.background_ontologies.values())
        self.background_term_count = sum(numpy.float_(results_array[:,-1]))

    def set_foreground_ontology(self, genes):
        '''
        For the passed set of genes of interest,
        get ontological terms from the GeneOntology database.
        '''
        if not self.go_accessor: self.go_accessor = GOAccessor()
        
        gene_names = [g.gene_name for g in genes]
        self.foreground_ontologies = self.go_accessor.get_ancestors_for_genes(gene_names)
        results_array = numpy.array(self.foreground_ontologies.values())
        self.foreground_term_count = sum(numpy.float_(results_array[:,-1]))
        
    def get_enriched_genes(self):
        '''
        For the filtered set of genes, extract a list of those 
        that are enriched, with p values and appearance percentages.
        
        P values are calculated using a binomial test versus
        an assumed Bernoulli experiment with expected ratios
        of appearance for a given term coming from the background set.
        '''
        genes, data_rows, selected_ids = self.filter_rows()
        enriched = self._get_enriched_genes(genes)
        return enriched
    
    def _get_enriched_genes(self, genes=None):
        if not self.background_ontologies: self.set_background_ontology()
        if genes: self.set_foreground_ontology(genes)
        enriched = {}
        for go_id, fg_info in self.foreground_ontologies.items():
            try: bg_info = self.background_ontologies[go_id]
            except KeyError:
                # Term didn't make the cut for the background. 
                # Assume the appearance in the foreground is the only occurence in the background 
                bg_info = fg_info
            bg_appearance = bg_info[-1:][0]/self.background_term_count
            p_val = binom_test(fg_info[-1:][0], n=self.foreground_term_count, p=bg_appearance)
            if p_val <= self.max_p_val:
                enriched[go_id] = fg_info + [p_val]
        return enriched
            