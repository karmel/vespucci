'''
Created on Sep 24, 2010

@author: karmel
'''
from optparse import OptionParser

class GlassOptionParser(OptionParser):
    options = None
    ''' List of optparse make_option objects. '''
    
    def __init__(self, option_list=None, **kwargs):
        OptionParser.__init__(self, option_list=option_list or self.options, **kwargs)