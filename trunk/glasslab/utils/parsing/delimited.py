'''
Created on Sep 24, 2010

@author: karmel

Functions and classes for parsing array-like delimited files.
'''
import numpy

class DelimitedFileParser(object):
    file_name = None
    file = None
    
    def __init__(self, file_name=''):
        super(DelimitedFileParser,self).__init__()
        self.file_name = file_name
        self.file = open(file_name)
        
    def get_array(self, delimiter='\t', strip=False):
        '''
        For initialized file, parse into numpy array and return.
        
        Omits empty lines and lines beginning with #
        '''
        if strip: clean = lambda x: x.strip('"').strip() 
        else: clean = lambda x: x
        return numpy.array([[clean(field) for field in line.strip('\n').split(delimiter)] 
                                for line in self.file if line.strip('\n') and line[:1] != '#' ])