'''
Created on Jun 4,2012

@author: karmel
'''
from datetime import datetime
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import numpy
import os

if __name__ == '__main__':
    raw_data = '''2012_04_02
96,86,142,54
99,84,93,94
2012_04_10
124,102,70,53
136,103,96,94
2012_04_17
151,119,119,49
133,81,88,118
2012_04_24
142,40,123,122
91,106,114,103
2012_05_01
133,164,141,66
87,137,103,115
2012_05_08
149,123,137,76
134,97,141,176
2012_05_15
173,149,138,138
119,135,125,159
2012_05_22
223,192,214,156
108,163,127,134
2012_05_25
212,387,162,220
127,133,153,186
2012_05_29
360,450,375,122
161,371,146,135
2012_06_01
450,441,600,153
228,408,393,156
2012_06_03
563,449,491,118
359,108,148,169'''
    
    raw_data = raw_data.split('\n')
    dates = [datetime.strptime(raw_data[x],'%Y_%m_%d') for x in xrange(0,len(raw_data),3)]
    set1 = numpy.array([map(int,raw_data[x].split(',')) for x in xrange(1,len(raw_data),3)]).T
    set2 = numpy.array([map(int,raw_data[x].split(',')) for x in xrange(2,len(raw_data),3)]).T
    
    grapher = SeqGrapher()
    ax = grapher.timeseries(dates, [set1, set2],
                   show_median=True, colors=['blue','red'], labels=['Control','TDB treated'],
                   title='Blood glucose values in NOD mice after TDB treatment', 
                   xlabel='Date', 
                   ylabel='Blood glucose (mg/dL, via Aviva AccuChek meter)',
                   show_plot=False,show_legend=True)
    dirpath = '/Users/karmel/Desktop/Projects/GlassLab/Notes_and_Reports/NOD_BALBc/TDB in vitro/'
    
    grapher.save_plot(os.path.join(dirpath, 'blood_glucose_values_after_tdb_with_delta_06_04_2012.png'))
    grapher.show_plot()
    