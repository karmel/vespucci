'''
Created on Nov 8, 2010

@author: karmel
'''
from glasslab.sequencing.datatypes.tag import GlassTag
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
from glasslab.config import current_settings
from glasslab.glassatlas.datatypes.transcript import CellTypeBase

class TranscribedRnaFromTagsParser(GlassOptionParser):
    options = [
               make_option('-c', '--cell_type',action='store', type='string', dest='cell_type', 
                           help='Cell type for this run? Options are: %s' % ','.join(CellTypeBase.get_correlations().keys())),
               make_option('-t', '--tag_table',action='store', type='string', dest='tag_table', 
                           help='Table name from which to load tags. Appended to schema if schema is included. Otherwise used as is.'),
               make_option('--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
               make_option('--skip_stitching',action='store_true', dest='skip_stitching',  
                           help='Should the stitching together of transcripts be skipped?'),
               make_option('--skip_associating',action='store_true', dest='skip_associating',  
                           help='Should the association of transcribed RNA to transcripts be skipped?'),
                ]
if __name__ == '__main__':
    parser = TranscribedRnaFromTagsParser()
    options, args = parser.parse_args()
    
    run_from_cammand_line = True 
    if not run_from_cammand_line:
        options.schema_name = 'thiomac_rnaseq_2010'
        options.tag_table = 'tag_wt_kla_1h'
    
    if options.cell_type: current_settings.CURRENT_CELL_TYPE = options.cell_type
    cell_base = CellTypeBase().get_cell_type_base(current_settings.CURRENT_CELL_TYPE)
    
    cell_base.glass_transcribed_rna.turn_off_autovacuum()    
    if options.tag_table:
        GlassTag._meta.db_table = options.schema_name and '%s"."%s' % (options.schema_name, options.tag_table) \
                                    or options.tag_table
        cell_base.glass_transcribed_rna.add_from_tags(GlassTag._meta.db_table)
        cell_base.glass_transcribed_rna.force_vacuum()
    
    if not options.skip_associating:
        # Associate first to optimize stitching.
        cell_base.glass_transcribed_rna.associate_transcribed_rna()
    
    if not options.skip_stitching:
        cell_base.glass_transcribed_rna.stitch_together_transcribed_rna()
        cell_base.glass_transcribed_rna.force_vacuum()
        
    cell_base.glass_transcribed_rna.turn_on_autovacuum()
    
