'''
Created on Sept 2, 2010

@author: karmel

There are a number of comparable samples in the nathanRosi and the yumikoMRL24 data.

Here we tease out some of the differences and similarities between the two.
'''
from datetime import timedelta
from glasslab.utils.data_types import Sample
from glasslab.microarrays.core.parse import MicroarrayImporter
from glasslab.microarrays.core.aggregation.aggregate import MicroarrayAggregator
import numpy
import re 
from glasslab.microarrays.experiments.yumikoMRL24 import mrl24
from glasslab.microarrays.experiments.nathanRosi import rosi
from glasslab.utils.geneannotation.geneontology import GOAccessor

class ExperimentSample(Sample):
    ''' 
    Custom sample with special type/time information. 
    '''
    def __init__(self, base_sample):
        ''' 
        From a base sample, parse out type info. 
        '''
        type, time = self.convert_type(base_sample.type)
        super(ExperimentSample, self).__init__(code = base_sample.code, 
                                        type = (type,time),
                                        control = (type == 'DMSO'))
        
    def convert_type(self, type):
        ''' 
        Type comes in as dmso-24hr, Rosi-24hr- convert to type and timestamp. 
        '''
        data_pieces = type.split('-')
        delta = timedelta(hours=int(re.search('\d+',data_pieces[1]).group(0)))
        return data_pieces[0], delta
    
    def __repr__(self):
        return '%s (%s)' % (self.type[0], str(self.type[1]))

class ExperimentMicroarrayAggregator(MicroarrayAggregator):
    gene_names = [
        # Immunological
        'Prkcb','Il6ra','4732429D16Rik','Havcr2','Il7r','Cd22','Cd109','Cd97',
        'Serpinf1','Ogn','Hsf2','Ear2','Ear12','Ear10','Ear4','Egln3','Tgm2',
        'Prf1','Lat','Hipk2','Ifngr2','Csf2rb','Il16',
        
        # Lipids
        'Sdpr','Acsl3','Scd1','Acsl4','Ctps','Cyb5r3','Cav1','Ch25h','Angptl4',
        'Pex11a','Lpcat3','Pld3','Pld2','Sort1','Acot1','Acaa2','Slco2b1','Adfp','Cd36',
        
        # Cardio/vascular/angio
        'Plxdc1','Nfam1','Flt1','F2r','Pdgfra','Mdk','Tnfsf15',
        ]
    
    def filter_rows(self): 
        genes, data_rows, selected_ids = self._filter_rows_by_log_differential(differential=.6, cols=[0,1,6])
        # return self._filter_for_specific_genes(gene_names=self.gene_names, limiting_ids=selected_ids)
        return genes, data_rows, selected_ids
    
    def sort_rows(self, genes, data_rows, selected_ids):
        return self._sort_rows_by_gene_processes(genes, data_rows, selected_ids)
        #return self._sort_rows_custom(genes, data_rows, selected_ids)
    
    def _sort_rows_custom(self, genes, data_rows, selected_ids):
        '''
        Sort rows according to gene function. Not implemented by default.
        '''
        # First sort names
        new_place_numbers = [(self.gene_names.index(g.gene_name), id) for id, g in enumerate(genes)]
        new_place_numbers.sort()
        place_numbers, ordered_gene_indices = zip(*new_place_numbers)
        
        # Align the two lists we want to keep in order
        matrix = numpy.array([genes, data_rows, selected_ids])
        matrix_sorted = map(lambda row: [row[i] for i in ordered_gene_indices], matrix)
        # And reorder the rows of the numpy array
        #data_rows = numpy.array([data_rows[i] for i in ordered_gene_indices])
        return matrix_sorted[0], matrix_sorted[1], matrix_sorted[2]
    
def get_aggregators_with_shared_genes():
    '''
    We want to compare Yumiko's Kdo2 data to Nathan's;
    however, each array has a different set of probes and observed genes.
    
    Here, therefore, we extract only those that are shared.
    '''
    # Get the full set of data from each file
    n_matrix, n_genes, n_samples = MicroarrayImporter('../nathanRosi/spann_agilent_PPARligand_norm.txt',
                                                      delimiter='\t').get_data()
    n_samples = [ExperimentSample(sample) for sample in n_samples]
    
    
    y_matrix, y_genes, y_samples = MicroarrayImporter('tanaka_norm_for_comparison.txt',delimiter='\t').get_data()
    y_samples = [ExperimentSample(sample) for sample in y_samples]
    
    # Filter out the non-shared rows in each set.
    # First we create a dictionary of all probes,
    # then keep only those that exist in both sets of data.
    gene_list = {}
    for i, g in enumerate(n_genes):
        gene_list[g.probe_id] = [i]    
    for i, g in enumerate(y_genes):
        try: gene_list[g.probe_id].append(i)
        except KeyError: gene_list[g.probe_id] = [i]
    shared_probes = filter(lambda k: len(gene_list[k]) == 2, gene_list)
    
    # Now, with the set of shared probe ids, get the corresponding
    # indices for the genes and matrix
    filtered_indices = numpy.array([gene_list[k] for k in shared_probes])
    n_indices = filtered_indices[:,0]
    y_indices = filtered_indices[:,1]

    n_matrix, n_genes = filter_shared_rows(n_matrix, n_genes, n_indices)
    y_matrix, y_genes = filter_shared_rows(y_matrix, y_genes, y_indices)
    
    n_sets = rosi._sort_samples_rosi_only(n_samples) 
    n_aggregator = rosi.sort_samples_into_aggregator(n_matrix, n_genes, n_samples, n_sets)
    y_aggregator = mrl24.sort_samples_into_aggregator(y_matrix, y_genes, y_samples)
    
    return n_aggregator, y_aggregator
        
def filter_shared_rows(matrix, genes, indices):
    genes = [genes[i] for i in indices]    
    matrix = numpy.array([matrix[i] for i in indices])    
    return matrix, genes
         
if __name__ == '__main__':
    n_aggregator, y_aggregator = get_aggregators_with_shared_genes()
    
    comparitor = ExperimentMicroarrayAggregator()
    for aggregator in (n_aggregator, y_aggregator):
        # Overwrite filter methods, so that nothing is filtered.
        #aggregator.filter_rows = lambda: True
        for analyzer in aggregator.subset_analyzers:
            comparitor.subset_analyzers.append(analyzer)
            #if analyzer.test_samples is None: analyzer.split_samples()
            # Now, with samples split,
    
    enriched = comparitor.get_enriched_genes()
    '''    
    comparitor.draw_heat_map(output_dir='yumikoMRL24', prefix='compare_nathan_yumiko_differential_processes', 
                                clustered=True, include_differentials=False,
                                include_annotation=True)
    '''