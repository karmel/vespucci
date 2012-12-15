'''
Created on Feb 23, 2011

@author: karmel

The refseq database is used for comparison and mapping to refseq during transcript stitching.
Here we set it up by calling the other scripts.
'''
from glasslab.utils.database import execute_query
from optparse import make_option
from glasslab.utils.scripting import GlassOptionParser
from glasslab.genomereference.datatypes import Chromosome,\
    SequenceTranscriptionRegion
from glasslab.glassatlas.pipeline.transcripts_from_tags import TranscriptsFromTagsParser

class SetUpRefseqDatabaseParser(GlassOptionParser):
    options = [
               make_option('-g', '--genome',action='store', type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm8, mm8r, mm9, hg18, hg18r, dm3'),
                ]

if __name__ == '__main__':
    parser = SetUpRefseqDatabaseParser()
    options, args = parser.parse_args()
    
    genome = parser.set_genome(options)
    
    print 'Creating views over refseq data...'
    chr_ids = Chromosome.objects.values_list('id', flat=True)
    q = ''
    for chr_id in chr_ids:
        q += """CREATE VIEW "{0}_{chr_id}" AS 
                    SELECT * FROM "{0}" WHERE chromosome_id = {chr_id};
                    """.format(SequenceTranscriptionRegion._meta.db_table, chr_id=chr_id)
    execute_query(q)
    
    print 'Adding data...'
    TranscriptsFromTagsParser(genome=options.genome, cell_type='refseq', 
                              schema_name=SequenceTranscriptionRegion.schema_name,
                              tag_table=SequenceTranscriptionRegion.table_name,
                              set_density=True, stitch=True, stitch_processes=2, 
                              draw_edges=True, score=True, no_extended_gaps=True)
    
    print 'Deleting views...'
    for chr_id in chr_ids:
        q += """DROP VIEW "{0}_{chr_id}";
                    """.format(SequenceTranscriptionRegion._meta.db_table, chr_id=chr_id)