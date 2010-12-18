'''
Created on Nov 8, 2010

@author: karmel
'''
from glasslab.sequencing.datatypes.tag import GlassTag
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
from glasslab.glassatlas.datatypes.transcribed_rna import GlassTranscribedRna

class TranscribedRnaFromTagsParser(GlassOptionParser):
    options = [
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
    
    GlassTranscribedRna.turn_off_autovacuum()    
    if options.tag_table:
        GlassTag._meta.db_table = options.schema_name and '%s"."%s' % (options.schema_name, options.tag_table) \
                                    or options.tag_table
        GlassTranscribedRna.add_from_tags(GlassTag._meta.db_table)
        GlassTranscribedRna.force_vacuum()
    
    if not options.skip_associating:
        # Associate first to optimize stitching.
        GlassTranscribedRna.associate_transcribed_rna()
    
    if not options.skip_stitching:
        GlassTranscribedRna.stitch_together_transcribed_rna()
    
    GlassTranscribedRna.force_vacuum()
    GlassTranscribedRna.turn_on_autovacuum()
    
