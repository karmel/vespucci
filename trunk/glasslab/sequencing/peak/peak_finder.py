'''
Created on Sep 23, 2010

@author: karmel

.. note::

    Experimental only. Not used by anything, and not operational.

'''
from __future__ import division
import numpy
from matplotlib import pyplot
from scipy import interpolate
from scipy.signal import cspline1d, cspline1d_eval

class PeakFinder(object):
    tags = None
    points = None
    averages = None
    splines = None
    
    def __init__(self):
        self.tags = {}
        self.points = {}
        self.averages = {}
        self.functions = {}
        self.smoothed_points = {}
        super(PeakFinder, self).__init__()
        
    def import_tag_file(self, chromosome, file_path):
        '''
        File_path is the path to a Homer-style tag file, with 
        one file per chromosome, tab-delimited with the following format::
        
            chr10-3021410-0 chr10   3021410 0       4
            chr10-3022289-0 chr10   3022289 0       1
            
        where the columns are ID, chromosome, 1-indexed start position, direction, and count.
        
        The file is read in and converted into a numpy array.
        '''
        f = open(file_path)
        self.tags[chromosome] = numpy.array([line.split('\t') for line in f])
    
    def adjust_to_center(self, chromosome, seq_length):
        '''
        Adjust the start points such that they represent the center of the 
        sequence in question, depending on the direction of the sequence.
        '''
        adjustment = seq_length//2
        # Shift to the right (positive direction) if the sequence is forward (dir = 0),
        # and to the left (negative direction) if the sequence is the complement (dir = 1).
        # If adjusted start is less than zero, use zero instead.
        self.tags[chromosome][:,2] = [max(0,int(start) + 
                                          (self.tags[chromosome][row][3] and -adjustment or adjustment))
                                            for row,start in enumerate(self.tags[chromosome][:,2])]  
        
        
    def convert_to_points(self, chromosome):
        '''
        From the set of adjusted tags, create x,y coordinate pairs.
        '''
        '''
        points = []
        for row, x in enumerate(self.tags[chromosome][:,2]):
            points += [int(x)]*int(self.tags[chromosome][row][4])
        self.points[chromosome] = points
        '''
        points = numpy.array([self.tags[chromosome][:,2], # x-coord: position
                             self.tags[chromosome][:,4]], dtype=numpy.int64) # y-coord: count
        
        # Combine points that have fallen onto the same place:
        unique = {}
        for i,point in enumerate(points[0]):
            try: unique[point] += points[1][i]
            except KeyError: unique[point] = points[1][i]
        x_coords, y_coords = [],[]
        for key, val in unique.items(): 
            x_coords.append(key), y_coords.append(val)
        points = numpy.array([x_coords, y_coords], dtype=numpy.int64)
        self.points[chromosome] = points[:,points[0].argsort()]
        
    def moving_average(self, chromosome, peak_width=100):
        '''
        Calculate moving average of width peak_width over points.
        '''
        x_start = self.points[chromosome][0][0]
        x_stop = self.points[chromosome][0][-1:][0]
        
        window_centers = []
        averages = []
        for window_open in xrange(x_start, x_stop, 6):
            window_close = window_open + peak_width
            window_center = window_open + peak_width/2
            condition = (self.points[chromosome][0] >= window_open) & (self.points[chromosome][0] < window_close)
            window_points = numpy.compress(condition,self.points[chromosome],axis=1)
            window_centers.append(window_center) 
            averages.append(sum(window_points[1])/peak_width)
        
        self.averages[chromosome] = numpy.array([window_centers,averages])
        
    def interpolate_points(self, chromosome, peak_width=100):
        x_start = self.points[chromosome][0][0]
        x_stop = self.points[chromosome][0][-1:][0]
        range = xrange(int(x_start + peak_width//2),int(x_stop + peak_width//2),peak_width)
        self.functions[chromosome] = interpolate.splrep(self.points[chromosome][0].tolist(),self.points[chromosome][1].tolist(),s=0)
        self.smoothed_points[chromosome] = (range,interpolate.splev(range, self.functions[chromosome]))
        
    def graph_points(self, chromosome, peak_width=100):
        '''
        For the set of x,y coords, plot for visualization.
        '''
        
        pyplot.plot(self.points[chromosome][0],self.points[chromosome][1],'o', 
                    self.smoothed_points[chromosome][0],self.smoothed_points[chromosome][1],'-')
        #pyplot.hist(self.points[chromosome], peak_width, label='Tag counts at positions for %s' % chromosome)
        #pyplot.plot(*self.averages[chromosome], label='Tag counts at positions for %s' % chromosome)
        
        pyplot.xlabel('Centered position on %s' % chromosome)
        pyplot.ylabel('Count of tags at position')
        pyplot.savefig('test.png')
        
        
if __name__ == '__main__':
    finder = PeakFinder()
    chr = 'chr10'
    finder.import_tag_file(chr, '/Users/karmel/Downloads/homer_output/chr10.tags.tsv')
    finder.adjust_to_center(chr, seq_length=36)
    finder.convert_to_points(chr)
    dict = {}
    '''
    for x in finder.points[chr][0]:
        try: 
            dict[x] +=1
            print x
        except KeyError: dict[x] = 1
    '''
    finder.interpolate_points(chr)
    finder.graph_points(chr)
    
    