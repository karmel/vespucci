'''
Created on Sep 24, 2010

@author: karmel
'''
from optparse import OptionParser
import os
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from glasslab.config import current_settings

class GlassOptionParser(OptionParser):
    options = None
    ''' List of optparse make_option objects. '''
    
    def __init__(self, option_list=None, **kwargs):
        OptionParser.__init__(self, option_list=option_list or self.options, **kwargs)

    def set_cell(self, options):
        cell_type = (options.cell_type and options.cell_type.lower()) or current_settings.CELL_TYPE.lower()
        cell_base = CellTypeBase().get_cell_type_base(cell_type)()
        current_settings.CELL_TYPE = cell_base.cell_type
        
        return cell_type, cell_base
    
    def set_genome(self, options):
        current_settings.GENOME = options.genome
        return current_settings.GENOME
    
def get_glasslab_path():
    import glasslab
    return os.path.dirname(glasslab.__file__)