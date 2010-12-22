'''
Created on Nov 8, 2010

@author: karmel
'''
from glasslab.glassatlas.datatypes.transcript import GlassTranscript,\
    FilteredGlassTranscript
from glasslab.sequencing.datatypes.tag import GlassTag
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
from datetime import datetime
import os

class TranscriptsFromTagsParser(GlassOptionParser):
    options = [
               make_option('-t', '--tag_table',action='store', type='string', dest='tag_table', 
                           help='Table name from which to load tags. Appended to schema if schema is included. Otherwise used as is.'),
               make_option('--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
               make_option('-o', '--output_dir',action='store', type='string', dest='output_dir',  
                           help='Output directory for bed file.'),
               make_option('--skip_stitching',action='store_true', dest='skip_stitching',  
                           help='Should the stitching together of transcripts be skipped?'),
               make_option('--skip_scoring',action='store_true', dest='skip_scoring',  
                           help='Should the scoring of transcripts be skipped?'),
               make_option('--skip_nucleotides',action='store_true', dest='skip_nucleotides',  
                           help='Should obtaining nucleotide sequences to transcripts be skipped?'),
                ]
if __name__ == '__main__':
    parser = TranscriptsFromTagsParser()
    options, args = parser.parse_args()
    
    run_from_cammand_line = True 
    if not run_from_cammand_line:
        options.schema_name = 'thiomac_groseq_nathan_2010_10'
        options.tag_table = 'tag_ncor_ko_kla_1h'
    
    #GlassTranscript.turn_off_autovacuum()    
    if options.tag_table:
        GlassTag._meta.db_table = options.schema_name and '%s"."%s' % (options.schema_name, options.tag_table) \
                                    or options.tag_table
        GlassTranscript.add_from_tags(GlassTag._meta.db_table)
        GlassTranscript.force_vacuum()
    
    if not options.skip_stitching:
        GlassTranscript.stitch_together_transcripts()
        GlassTranscript.force_vacuum()
    #if not options.skip_nucleotides:
        #GlassTranscript.associate_nucleotides()
    if not options.skip_scoring:
        GlassTranscript.set_scores()
        
    if options.output_dir:
        file_name = 'Glass_Transcripts_%s.bed' % datetime.now().strftime('%Y_%m_%d')
        full_path = os.path.join(options.output_dir, file_name)
        FilteredGlassTranscript.generate_bed_file(full_path)
        
    #GlassTranscript.turn_on_autovacuum()
    
