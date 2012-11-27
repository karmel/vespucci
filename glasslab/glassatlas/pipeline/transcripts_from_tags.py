'''
Created on Nov 8, 2010

@author: karmel
'''
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from glasslab.sequencing.tag import GlassTag
from optparse import make_option
from glasslab.config import current_settings
from glasslab.utils.database import discard_temp_tables
from glasslab.glassatlas.pipeline.base_parser import GlassAtlasParser

class TranscriptsFromTagsParser(GlassAtlasParser):
    options = [
               make_option('-g', '--genome',action='store', type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm8, mm8r, mm9, hg18, hg18r'),
               make_option('-c', '--cell_type',action='store', type='string', dest='cell_type', 
                           help='Cell type for this run? Options are: %s' % ','.join(CellTypeBase.get_correlations().keys())),
               make_option('-t', '--tag_table',action='store', type='string', dest='tag_table', 
                           help='Table name from which to load tags. Appended to schema if schema is included. Otherwise used as is.'),
               make_option('-s', '--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
               make_option('-o', '--output_dir',action='store', type='string', dest='output_dir',  
                           help='Output directory for bed file.'),
               make_option('-p','--processes',action='store', dest='processes', default=None,  
                           help='How many processes can be used?'),
               make_option('--stitch_processes',action='store', dest='stitch_processes', default=None,  
                           help='How many processes can be used during stitching, which is memory-intensive?'),
               
               make_option('--stitch',action='store_true', dest='stitch',  
                           help='Should transcripts be stitched together?'),
               make_option('--set_density',action='store_true', dest='set_density',  
                           help='Set density? Performed with tag stitching, or separately if --stitch=False.'),
               make_option('--draw_edges',action='store_true', dest='draw_edges',  
                           help='Should the edges between transcripts be created and saved?'),
               make_option('--score',action='store_true', dest='score',  
                           help='Should transcripts be stored?'),
               make_option('--no_extended_gaps',action='store_true', dest='no_extended_gaps',  
                           help='Should extended gaps (i.e., under RefSeq regions) be allowed?'),
               make_option('--extension_percent',action='store', dest='extension_percent', type='string', default='.2',
                           help='What percent of a RefSeq gene body can be automatically stitched over? Expects float, default: .2 (20%)'),
               make_option('--staging',action='store_true', dest='staging', default=False,  
                           help='Use the transcript database with the suffix _staging?'),
                ]

if __name__ == '__main__':
    parser = TranscriptsFromTagsParser()
    options, args = parser.parse_args()
    
    if options.processes:
        current_settings.ALLOWED_PROCESSES = int(options.processes)
    
    cell_type, cell_base = parser.set_cell(options)
    parser.set_genome(options)
    
    allow_extended_gaps = True
    if options.no_extended_gaps: allow_extended_gaps = False
    
    if options.staging: current_settings.STAGING = current_settings.STAGING_SUFFIX

    if options.tag_table:
        GlassTag._meta.db_table = options.schema_name and '%s"."%s' % (options.schema_name, options.tag_table) \
                                    or options.tag_table
        cell_base.glass_transcript.add_from_tags(GlassTag._meta.db_table)
        
    if options.stitch:
        if options.stitch_processes:
            curr_processes = current_settings.ALLOWED_PROCESSES 
            current_settings.ALLOWED_PROCESSES = int(options.stitch_processes)
    
        cell_base.glass_transcript.stitch_together_transcripts(
                        allow_extended_gaps=allow_extended_gaps, 
                        extension_percent=options.extension_percent, 
                        set_density=options.set_density)
    
        if options.stitch_processes:
            current_settings.ALLOWED_PROCESSES = curr_processes
    
    elif options.set_density:
        cell_base.glass_transcript.set_density(allow_extended_gaps=allow_extended_gaps,
                                               extension_percent=options.extension_percent)
    
    if options.draw_edges:
        cell_base.glass_transcript.draw_transcript_edges()
    
    if options.score:
        cell_base.glass_transcript.set_scores()
        
    if options.output_dir:
        cell_base.filtered_glass_transcript.generate_bed_file(options.output_dir)
        
    discard_temp_tables()