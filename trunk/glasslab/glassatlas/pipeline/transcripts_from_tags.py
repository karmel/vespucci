'''
Created on Nov 8, 2010

@author: karmel
'''
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from glasslab.sequencing.datatypes.tag import GlassTag
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
from glasslab.config import current_settings
from datetime import datetime
import os

class TranscriptsFromTagsParser(GlassOptionParser):
    options = [
               make_option('-c', '--cell_type',action='store', type='string', dest='cell_type', 
                           help='Cell type for this run? Options are: %s' % ','.join(CellTypeBase.get_correlations().keys())),
               make_option('-t', '--tag_table',action='store', type='string', dest='tag_table', 
                           help='Table name from which to load tags. Appended to schema if schema is included. Otherwise used as is.'),
               make_option('-s', '--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
               make_option('-o', '--output_dir',action='store', type='string', dest='output_dir',  
                           help='Output directory for bed file.'),
               make_option('--skip_stitching',action='store_true', dest='skip_stitching',  
                           help='Should the stitching together of transcripts be skipped?'),
               make_option('--draw_edges',action='store_true', dest='draw_edges',  
                           help='Should the edges between transcripts be created and saved?'),
               make_option('--reset_score_thresholds',action='store_true', dest='reset_score_thresholds',  
                           help='Should the expected score thresholds for each chromosome and strand be reset?'),
               make_option('--skip_scoring',action='store_true', dest='skip_scoring',  
                           help='Should the scoring of transcripts be skipped?'),
               make_option('--associate_nucleotides',action='store_true', dest='associate_nucleotides',  
                           help='Should obtaining nucleotide sequences to transcripts be attempted?'),
               make_option('--skip_reassociation',action='store_true', dest='skip_reassociation',  
                           help='Should reassociation of peak features to transcripts be skipped?'),
               make_option('--allow_extended_gaps',action='store_true', dest='allow_extended_gaps',  
                           help='Should extended gaps (i.e., under RefSeq regions) be allowed?'),
                ]
if __name__ == '__main__':
    parser = TranscriptsFromTagsParser()
    options, args = parser.parse_args()
    
    run_from_cammand_line = True 
    if not run_from_cammand_line:
        options.schema_name = 'thiomac_groseq_nathan_2010_10'
        options.tag_table = 'tag_ncor_ko_kla_1h'
    
    if options.cell_type: current_settings.CURRENT_CELL_TYPE = options.cell_type
    cell_base = CellTypeBase().get_cell_type_base(current_settings.CURRENT_CELL_TYPE)()
    
    cell_base.glass_transcript.turn_off_autovacuum()    
    if options.tag_table:
        GlassTag._meta.db_table = options.schema_name and '%s"."%s' % (options.schema_name, options.tag_table) \
                                    or options.tag_table
        cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        cell_base.glass_transcript.force_vacuum()
    
    if not options.skip_stitching:
        allow_extended_gaps = False
        if options.allow_extended_gaps: allow_extended_gaps = True
        cell_base.glass_transcript.stitch_together_transcripts(allow_extended_gaps=allow_extended_gaps)
        cell_base.glass_transcript.force_vacuum()

    if options.draw_edges:
        cell_base.glass_transcript.draw_transcript_edges()
        cell_base.glass_transcript.force_vacuum()
    
    if options.associate_nucleotides:
        cell_base.glass_transcript.associate_nucleotides()
    
    if options.reset_score_thresholds:
        cell_base.glass_transcript.set_score_thresholds()
        
    if not options.skip_scoring:
        cell_base.glass_transcript.set_scores()
        
    if not options.skip_reassociation:
        cell_base.peak_feature.update_peak_features_by_transcript()
        cell_base.glass_transcript.mark_all_reloaded()
        
    if options.output_dir:
        cell_base.filtered_glass_transcript.generate_bed_file(options.output_dir)
        
    cell_base.glass_transcript.turn_on_autovacuum()
    
