'''
Created on Nov 8, 2010

@author: karmel
'''
from glasslab.glassatlas.datatypes.transcript import GlassTranscript
from glasslab.sequencing.datatypes.tag import GlassTag
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option

class TranscriptsFromTagsParser(GlassOptionParser):
    options = [
               make_option('-t', '--tag_table',action='store', type='string', dest='tag_table', 
                           help='Table name from which to load tags. Appended to schema if schema is included. Otherwise used as is.'),
               make_option('--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
                ]
if __name__ == '__main__':
    parser = TranscriptsFromTagsParser()
    options, args = parser.parse_args()
    
    run_from_cammand_line = True 
    if not run_from_cammand_line:
        options.schema_name = 'thiomac_groseq_nathan_2010_10'
        options.tag_table = 'tag_ncor_ko_kla_1h'
        
    if options.tag_table:
        GlassTag._meta.db_table = options.schema_name and '%s"."%s' % (options.schema_name, options.tag_table) \
                                    or options.tag_table
        GlassTranscript.add_transcripts_from_tags(GlassTag._meta.db_table)
        
    GlassTranscript.stitch_together_transcripts()
    GlassTranscript.set_scores()
    GlassTranscript.delete_invalid_transcripts()
