'''
Created on Jun 26, 2012

@author: karmel
'''
from __future__ import division 
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
from matplotlib import pyplot
import numpy
from scipy import stats
import math


class BasepairCounter(SeqGrapher):
    '''
    Used for drawing tags-per-basepair charts.
    '''
    from_bp = -500
    to_bp = 2000
    
    def __init__(self, from_bp=None, to_bp=None):
        self.from_bp = from_bp or self.from_bp
        self.to_bp = to_bp or self.to_bp
        
    def plot_tags_per_basepair(self, data, labels,
                               title='', xlabel='',ylabel='',
                               window_len=100, ymax_percentile=99.5,
                               tag_scalars=None, show_moving_average=True,
                               show_count = False):
        '''
        Given a list of data frames with cols basepair and tag_count, 
        graph each as a line.
        
        '''
        
        fig = pyplot.figure(figsize=[12,6])
        # Set up plot
        ax = pyplot.subplot(111)
        ax.set_xlim([self.from_bp, self.to_bp])
        
        all_y_vals = []
        colors = self.get_colors(len(data))
        if show_moving_average:
            for i, dataset in enumerate(data):
                try: dataset['tag_count'] = dataset['tag_count']*tag_scalars[i]
                except TypeError: dataset['tag_count'] = dataset['tag_count']*(tag_scalars or 1)
                
                all_y_vals.extend(dataset['tag_count'])
                pyplot.plot(dataset['basepair'], dataset['tag_count'], '.', 
                            markeredgecolor=colors[i], markerfacecolor='None', 
                            alpha=.2, markeredgewidth=.5)
                
        # Another loop, since we want all the lines above all the circles
        for i, dataset in enumerate(data):
            # Graph fit line
            line_type = i % 2 and '--' or '-'
            if show_moving_average:
                x, y = self.smooth(dataset['basepair'], dataset['tag_count'], window_len=window_len)
            else: x, y = dataset['basepair'], dataset['tag_count']
            pyplot.plot(x, y, line_type, color=colors[i], label=labels[i], linewidth=2)
            
            if show_count:
                pyplot.text(.1, .9, 'Total count: %d' % len(dataset), color=colors[i],
                            transform=ax.transAxes)
                
        # Limit yaxis by percentile if desired:
        if show_moving_average and ymax_percentile:
            ymax = stats.scoreatpercentile(all_y_vals, ymax_percentile) 
            ax.set_ylim([0, int(math.ceil(ymax))])

        
        pyplot.legend()
        self.add_title(title or 'Tag counts around transcription start sites', ax)
        self.add_axis_labels(xlabel or 'Basepairs from TSS', 
                             ylabel or 'Normalized number of tag starts')
        
        return ax    
            
    def smooth(self, x, y, window_len=100):
        '''
        Do a moving average smoothing of the data.
        x is basepairs; y is tag counts, so first we need to fill out tag counts
        to ensure we have a value for every x.
        
        '''
        offset = min(x)
        indexed = numpy.zeros(max(x) - min(x) + 1) # Inclusive range of zeros
        for bp, tag_count in zip(x,y):
            indexed[bp - offset] = tag_count
        
        reshaped = numpy.r_[2*indexed[0]-indexed[window_len-1::-1],
                            indexed,
                            2*indexed[-1]-indexed[-1:-window_len:-1]]
        window = numpy.ones(window_len,'d')
        smoothed = numpy.convolve(window/window.sum(),reshaped,mode='same')
        return xrange(min(x), max(x) + 1), smoothed[window_len:-window_len+1]
    
    def get_tag_scalars(self, totals, normalize_to=10**7):
        '''
        Get scalars for normalizing total tags to specified value.
        
        Totals can be a single value or a list.
        
        Returns an array or scalars.
        '''
        
        try: 
            totals[0]
            totals = numpy.array(totals)
        except TypeError: pass
        return normalize_to/totals
        
        
        