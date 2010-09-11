'''
Created on Jul 27, 2010

@author: karmel

In this experiment, a macrophage cell line (RAW264.7 or simply RAW cells) have been treated with 
the compound Lipopolysaccharide (a.k.a. LPS, another alias is "Kdo2 lipid A", 
which is a purified component of LPS), which is a component of the cell wall of gram negative bacteria.  
This essentially induces an innate immune response in the macrophage, and is used for studying inflammation.  
For this experiment, total RNA was extracted from the cells at several time points in mock treated or 
LPS treated cells, and then quantified using gene expression microarrays.  
The experiment was repeated several times as well, in order to get an idea of how much 
variation there is in the measurements.

'''
from datetime import timedelta
from glasslab.utils.data_types import Sample
from glasslab.microarrays.core.parse import MicroarrayImporter
from glasslab.microarrays.core.aggregate import MicroarrayAggregator
import numpy

class LPSSample(Sample):
    ''' 
    Custom sample with special type/time information. 
    '''
    def __init__(self, base_sample):
        ''' 
        From a base sample, parse out type info. 
        '''
        type, time = self.convert_type(base_sample.type)
        super(LPSSample, self).__init__(code = base_sample.code, 
                                        type = (type,time),
                                        control = (type == 'NOTX'))
        
    def convert_type(self, type):
        ''' 
        Type comes in as NOTX-0.5h, LPS-1h -- convert to type and timestamp. 
        '''
        data_pieces = type.split('-')
        delta = timedelta(hours=float(data_pieces[1][:-1]))
        return data_pieces[0], delta
    
    def __repr__(self):
        return '%s (%s)' % (self.type[0], str(self.type[1]))
    
if __name__ == '__main__':
    matrix, genes, samples = MicroarrayImporter('lipid_maps.csv',delimiter=',').get_data()
    samples = [LPSSample(sample) for sample in samples]
    
    # Now that we have like samples combined, split into several analyzers,
    # one for each timestamp.
    sets = {}
    for i,sample in enumerate(samples):
        try: sets[sample.type[1]].append(i)
        except KeyError: sets[sample.type[1]] = [i]
    timestamps = sets.keys()
    timestamps.sort()
    
    aggregator = MicroarrayAggregator()
    for key in timestamps:
        set = sets[key]
        sub_matrix = numpy.transpose(numpy.array([matrix[:,col] for col in set]))
        sub_samples = [samples[col] for col in set]
        aggregator.add_data_set(sub_matrix, genes, sub_samples)
    
    aggregator.draw_heat_map(clustered=True, prefix='lps')
    aggregator.draw_heat_map(clustered=False, prefix='lps')
