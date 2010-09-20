'''
Created on Sept 2, 2010

@author: karmel

Experiment performed by Nathan Spann, 2009-08-05

This experiment was designed to evaluate the performance of rosiglitazone 
(a PPAR{gamma} ligand in the thiazolidinedione flass of antidiabetic agents),
GW1929 (another PPAR{gamma} ligand with very high binding affinity),
and GW0072 (a PPAR{gamma} modulator, with 15-20% of rosi's efficiency,
but allegedly fewer side effects like weight gain and edema)
during inflammation induced by Kdo2.

The setup: Illumina hybridization

The samples:

#. DMSO (control), 8h
#. DMSO (control), 8h
#. Kdo2, 6h
#. Kdo2, 6h
#. Rosi + Kdo2, 8h
#. GW1929 + Kdo2, 8h
#. GW0072 + Kdo2, 8h
#. GW0072 + Kdo2, 8h
#. DMSO (control), 24h
#. DMSO (control), 24h
#. Rosi, 24h
#. Rosi, 24h
#. GW1929, 24h
#. GW1929, 24h
#. GW0072, 24h

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
        Type comes in as dmso-24hr, Rosi-24hr- convert to type and timestamp. 
        '''
        data_pieces = type.split('-')
        delta = timedelta(hours=int(re.search('\d+',data_pieces[1]).group(0)))
        return data_pieces[0], delta
    
    def __repr__(self):
        return '%s (%s)' % (self.type[0], str(self.type[1]))

class ExperimentMicroarrayAggregator(MicroarrayAggregator):
    #def filter_rows(self): 
    #    return self._filter_rows_by_log_differential(differential=0.25)
        
    def sort_rows(self, genes, data_rows, selected_ids): 
        return self._sort_rows_by_gene_function(genes, data_rows, selected_ids)
        
def _sort_samples_rosi_only(samples):
    sets = {'1 DMSO-6h vs. Kdo2-6h': [],
            '2 DMSO-6h vs. Rosi+Kdo2-6h': [],
            '5 DMSO-24h vs. Rosi-24h': [],
            }
    for i,sample in enumerate(samples):
        if sample.type == ('DMSO',timedelta(hours=24)):
            sets['5 DMSO-24h vs. Rosi-24h'].append(i)
        elif sample.type == ('Rosi',timedelta(hours=24)):
            sets['5 DMSO-24h vs. Rosi-24h'].append(i)
        elif sample.type == ('DMSO',timedelta(hours=6)):
            sets['1 DMSO-6h vs. Kdo2-6h'].append(i)
            sets['2 DMSO-6h vs. Rosi+Kdo2-6h'].append(i)
        elif sample.type == ('Kdo2',timedelta(hours=6)):
            sets['1 DMSO-6h vs. Kdo2-6h'].append(i)
        elif sample.type == ('Rosi+Kdo2',timedelta(hours=6)):
            sets['2 DMSO-6h vs. Rosi+Kdo2-6h'].append(i)
    return sets

def _sort_samples(samples):
    '''
    We want to perform several different side-by-side comparisons:
    
    #. DMSO-24h vs. Rosi-24h
    #. DMSO-24h vs. GW1929-24h
    #. DMSO-24h vs. GW0072-24h
    #. DMSO-6h vs. Kdo2-6h
    #. DMSO-6h vs. Rosi+Kdo2-6h
    #. DMSO-6h vs. GW1929+Kdo2-6h
    #. DMSO-6h vs. GW0072+Kdo2-6h
    
    So everything is special-cased.
    '''
    
    sets = {'1 DMSO-6h vs. Kdo2-6h': [],
            '2 DMSO-6h vs. Rosi+Kdo2-6h': [],
            '3 DMSO-6h vs. GW1929+Kdo2-6h': [],
            '4 DMSO-6h vs. GW0072+Kdo2-6h': [],
            '5 DMSO-24h vs. Rosi-24h': [],
            '6 DMSO-24h vs. GW1929-24h': [],
            '7 DMSO-24h vs. GW0072-24h': [],
            }
    for i,sample in enumerate(samples):
        if sample.type == ('DMSO',timedelta(hours=24)):
            sets['5 DMSO-24h vs. Rosi-24h'].append(i)
            sets['6 DMSO-24h vs. GW1929-24h'].append(i)
            sets['7 DMSO-24h vs. GW0072-24h'].append(i)
        elif sample.type == ('Rosi',timedelta(hours=24)):
            sets['5 DMSO-24h vs. Rosi-24h'].append(i)
        elif sample.type == ('GW1929',timedelta(hours=24)):
            sets['6 DMSO-24h vs. GW1929-24h'].append(i)
        elif sample.type == ('GW0072',timedelta(hours=24)):
            sets['7 DMSO-24h vs. GW0072-24h'].append(i)
        elif sample.type == ('DMSO',timedelta(hours=6)):
            sets['1 DMSO-6h vs. Kdo2-6h'].append(i)
            sets['2 DMSO-6h vs. Rosi+Kdo2-6h'].append(i)
            sets['3 DMSO-6h vs. GW1929+Kdo2-6h'].append(i)
            sets['4 DMSO-6h vs. GW0072+Kdo2-6h'].append(i)
        elif sample.type == ('Kdo2',timedelta(hours=6)):
            sets['1 DMSO-6h vs. Kdo2-6h'].append(i)
        elif sample.type == ('Rosi+Kdo2',timedelta(hours=6)):
            sets['2 DMSO-6h vs. Rosi+Kdo2-6h'].append(i)
        elif sample.type == ('GW1929+Kdo2',timedelta(hours=6)):
            sets['3 DMSO-6h vs. GW1929+Kdo2-6h'].append(i)
        elif sample.type == ('GW0072+Kdo2',timedelta(hours=6)):
            sets['4 DMSO-6h vs. GW0072+Kdo2-6h'].append(i)
        
    return sets

def sort_samples_into_aggregator(matrix, genes, samples, sets):
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
    matrix, genes, samples = MicroarrayImporter('spann_agilent_PPARligand_norm.txt',
                                                delimiter='\t').get_data()
    samples = [ExperimentSample(sample) for sample in samples]
    
    sets = _sort_samples(samples)
    aggregator = sort_samples_into_aggregator(matrix, genes, samples, sets)
    aggregator.draw_heat_map(output_dir='nathanRosi', prefix='nathanRosi', 
                                clustered=True, include_differentials=True,
                                include_annotation=False)
