'''
Created on Sep 24, 2010

@author: karmel
'''
from optparse import OptionParser
import os
from vespucci.config import current_settings

class VespucciOptionParser(OptionParser):
    options = None
    ''' List of optparse make_option objects. '''
    
    def __init__(self, option_list=None, **kwargs):
        OptionParser.__init__(self, option_list=option_list or self.options, **kwargs)

    def set_cell(self, options):
        from vespucci.atlas.datatypes.transcript import CellTypeBase
        cell_type = (options.cell_type and options.cell_type.lower()) or current_settings.CELL_TYPE.lower()
        cell_base = CellTypeBase().get_cell_type_base(cell_type)()
            
        return current_settings.CELL_TYPE, cell_base
    
    def set_genome(self, options):
        current_settings.GENOME = options.genome
        
        # Update table names for loaded classes
        from vespucci.genomereference import datatypes
        for m in (datatypes.Chromosome, datatypes.SequenceIdentifier,
                  datatypes.SequenceTranscriptionRegion,
                  datatypes.NonCodingRna, datatypes.NonCodingTranscriptionRegion,
                  datatypes.SequencingRun):
            m.set_db_table()
        return current_settings.GENOME
    
def get_vespucci_path():
    import vespucci
    return os.path.dirname(vespucci.__file__)
