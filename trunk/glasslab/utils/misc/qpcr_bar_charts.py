'''
Created on Sep 7, 2011

@author: karmel

Script for drawing bar charts with error bars from qPCR exports.
'''
import sys
from glasslab.utils.parsing.delimited import DelimitedFileParser
import matplotlib.pyplot as plt
import numpy
from operator import itemgetter
from itertools import groupby

def draw_bar_charts(data, remove_outliers=0):
    # First, mask any undetermined or 0 vals:
    data = data[data['C_'] > 0]
    primers = list(map(itemgetter(0), groupby(data['Target Name'])))
    samples = list(map(itemgetter(0), groupby(sorted(data['Sample Name']))))
    
    samples.sort(reverse=True)
    
    # Set up housekeeping data
    base_dataset = data[data['Target Name'] == primers[0]]
    base_means, base_std, base_counts = get_stats(base_dataset, samples, remove_outliers)
    
    width = 0.35 # The width of the bars
    fig = plt.figure(figsize=(10,6))
    fig.subplots_adjust(hspace=.5)
    for i, primer in enumerate(primers[1:]):
        dataset = data[data['Target Name'] == primer]
        ind = numpy.arange(len(samples)) # The x locations for the groups
    
        means, std, counts = get_stats(dataset, samples, remove_outliers)
        
        # First adjust by paired housekeeping gene for this sample-- this is deltaCT
        means = means - base_means
        
        # Then adjust by one calibration value-- this is deltadeltaCT
        norm_factor = means[0] # Assuming this is control treatment
        
        # Then get the deltaCT standard error-- this is (std dev of the sample + std dev of base)/sqrt(total samples being averaged)
        std_err = (std + base_std)/(counts + base_counts)**.5
        
        rq = 2**-(means - norm_factor)
        rq_max = 2**-(means - std_err - norm_factor)
        rq_min = 2**-(means + std_err - norm_factor)
        
        error_bars = numpy.array([(rq - rq_min).tolist(), (rq_max - rq).tolist()])
        
        ax = fig.add_subplot((len(primers)-1)*100 + 11 + i)
        ax.plot((ind[0] -1, ind[-1:][0] + 1), (0,0), '-', color='black')
        ax.bar(ind, rq, width, yerr=error_bars)
        ax.set_ylabel('RQ')
        ax.set_title(primer)
        ax.set_xticks(ind+width/2)
        # Alternate labels for readability
        #if i % 2: ax.set_xticklabels([n % 2 and s or '' for n, s in enumerate(samples)])
        #else: ax.set_xticklabels([(not n % 2) and s or '' for n, s in enumerate(samples)])
        
        # Or all labels
        ax.set_xticklabels(samples)
    plt.show()

def get_stats(dataset, samples, remove_outliers=0):
    means = numpy.array([dataset[dataset['Sample Name'] == sample]['C_'].mean() for sample in samples])
    std = numpy.array([dataset[dataset['Sample Name'] == sample]['C_'].std() for sample in samples])
    counts = numpy.array([len(dataset[dataset['Sample Name'] == sample]) for sample in samples])
    
    if remove_outliers:
        # Remove up to remove_outliers outliers
        to_remove = []
        for k, sample in enumerate(samples):
            diffs = [(abs(row['C_'] - means[k]), i) for i, row in enumerate(dataset) if row['Sample Name'] == sample]
            diffs.sort(reverse=True)
            to_remove = to_remove + list(zip(*diffs[:remove_outliers])[1])
    
        dataset = numpy.delete(dataset, to_remove, axis=0)
        means = numpy.array([dataset[dataset['Sample Name'] == sample]['C_'].mean() for sample in samples])
        std = numpy.array([dataset[dataset['Sample Name'] == sample]['C_'].std() for sample in samples])
        counts = numpy.array([len(dataset[dataset['Sample Name'] == sample]) for sample in samples])
    return means, std, counts
    
            
if __name__ == '__main__':
    if len(sys.argv) > 1: file_name = sys.argv[1]
    else:
        file_name = '/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Thyroid/qPCR/T3 treated cells/RAW cells 2011-10-08/T3_treated_RAW_2011_10_08_data.txt'

    
    parser = DelimitedFileParser(file_name=file_name, header=True)
    parser.convert_line_endings()
    data = parser.get_array()
    
    draw_bar_charts(data, remove_outliers=0)