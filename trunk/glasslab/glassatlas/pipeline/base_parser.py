'''
Created on Sep 24, 2010

@author: karmel
'''
from glasslab.config import current_settings
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from glasslab.utils.scripting import GlassOptionParser


class GlassAtlasParser(GlassOptionParser):
    def set_cell(self, options):
        cell_type = options.cell_type.lower() or current_settings.CELL_TYPE.lower()
        cell_base = CellTypeBase().get_cell_type_base(cell_type)()
        current_settings.CELL_TYPE = cell_base.cell_type
        
        return cell_type, cell_base
    
    def set_genome(self, options):
        current_settings.GENOME = options.genome
        return current_settings.GENOME