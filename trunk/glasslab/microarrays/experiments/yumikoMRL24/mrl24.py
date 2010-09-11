'''
Created on Aug 31, 2010

@author: karmel

Experiment performed by Yumiko Tanaka, 2010-07-14

This experiment was designed to evaluate the performance of MRL24
during inflammation induced by Kdo2.

The setup: Illumina hybridization, initial analysis done by 
Roman Sasik at Corgon.

The samples:

#. MRL24, 24h
#. Kdo2, 6h
#. MRL24 + Kdo2, 2h + 6h (8h total)
#. DMSO (control), 8h
#. DMSO (control), 24h
#. MRL24, 24h (replicate) 
#. Kdo2, 6h (replicate)
#. MRL24+Kdo2, 8h (replicate)

'''
from datetime import timedelta
from glasslab.utils.data_types import Sample
from glasslab.microarrays.core.parse import MicroarrayImporter
from glasslab.microarrays.core.aggregation.aggregate import MicroarrayAggregator
import numpy
import re 

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
        Type comes in as MRL24-24hours, DMSO-24hours- convert to type and timestamp. 
        '''
        data_pieces = type.split('-')
        delta = timedelta(hours=int(re.search('\d+',data_pieces[1]).group(0)))
        return data_pieces[0], delta
    
    def __repr__(self):
        return '%s (%s)' % (self.type[0], str(self.type[1]))

class ExperimentMicroarrayAggregator(MicroarrayAggregator):
    def filter_rows(self): 
        return self._filter_rows_by_log_differential(differential=0.25)
        
    def sort_rows(self, genes, data_rows, selected_ids): 
        return self._sort_rows_by_gene_function(genes, data_rows, selected_ids)
        

def sort_samples_into_aggregator(matrix, genes, samples):
    
    '''
    We want to perform several different side-by-side comparisons:
    
    #. DMSO-24h vs. MRL24-24h
    #. DMSO-8h vs. Kdo2-6h
    #. DMSO-8h vs. MRL24+Kdo2-8h
    
    So everything is special-cased.
    '''
    sets = {'1 DMSO-8h vs. Kdo2-6h': [],
            '2 DMSO-8h vs. MRL24+Kdo2-8h': [],
            '3 DMSO-24h vs. MRL24-24h': [],
            }
    for i,sample in enumerate(samples):
        if sample.type == ('DMSO',timedelta(hours=24)):
            sets['3 DMSO-24h vs. MRL24-24h'].append(i)
        elif sample.type == ('MRL24',timedelta(hours=24)):
            sets['3 DMSO-24h vs. MRL24-24h'].append(i)
        elif sample.type == ('DMSO',timedelta(hours=6)):
            sets['1 DMSO-8h vs. Kdo2-6h'].append(i)
            sets['2 DMSO-8h vs. MRL24+Kdo2-8h'].append(i)
        elif sample.type == ('Kdo2',timedelta(hours=6)):
            sets['1 DMSO-8h vs. Kdo2-6h'].append(i)
        elif sample.type == ('MRL24+Kdo2',timedelta(hours=8)):
            sets['2 DMSO-8h vs. MRL24+Kdo2-8h'].append(i)
            
    set_keys = sets.keys()
    set_keys.sort()
    
    aggregator = ExperimentMicroarrayAggregator()
    for key in set_keys:
        set = sets[key]
        sub_matrix = numpy.transpose(numpy.array([matrix[:,col] for col in set]))
        sub_samples = [samples[col] for col in set]
        aggregator.add_data_set(sub_matrix, genes, sub_samples, normalize=False)
    
    return aggregator
     
if __name__ == '__main__':
    matrix, genes, samples = MicroarrayImporter('tanaka_norm.txt',delimiter='\t').get_data()
    samples = [ExperimentSample(sample) for sample in samples]
    
    aggregator = sort_samples_into_aggregator(matrix, genes, samples)
    aggregator.draw_heat_map(output_dir='yumikoMRL24', prefix='yumikoMRL24_versus', 
                                clustered=True, include_differentials=True,
                                include_annotation=True)
    
