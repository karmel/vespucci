'''
Created on Sep 24, 2010

@author: karmel
'''
from optparse import OptionParser
import os

class GlassOptionParser(OptionParser):
    options = None
    ''' List of optparse make_option objects. '''
    
    def __init__(self, option_list=None, **kwargs):
        OptionParser.__init__(self, option_list=option_list or self.options, **kwargs)


def get_glasslab_path():
    import glasslab
    GLASSLAB_PATH = os.path.basename(glasslab.__file__)
