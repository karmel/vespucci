'''
Created on Feb 23, 2011

@author: karmel

The refseq database is used for comparison and mapping 
to refseq during transcript stitching.
Here we set it up by calling the other scripts.
'''
from vespucci.utils.database import execute_query
from optparse import make_option
from vespucci.utils.scripting import VespucciOptionParser, get_vespucci_path
from vespucci.genomereference.datatypes import Chromosome, \
    SequenceTranscriptionRegion
import subprocess
import os
from vespucci.config import current_settings

class SetUpRefseqDatabaseParser(VespucciOptionParser):
    options = [
               make_option('-g', '--genome', action='store',
                           type='string', dest='genome', default='mm9',
                           help='Currently supported: mm9, dm3'),
                ]

if __name__ == '__main__':
    parser = SetUpRefseqDatabaseParser()
    options, args = parser.parse_args()

    genome = parser.set_genome(options)

    print('Creating tables for refseq data...')
    chr_ids = Chromosome.objects.values_list('id', flat=True)
    q = ''
    for chr_id in chr_ids:
        q += """CREATE TABLE "{0}_{chr_id}" AS 
                    SELECT * FROM "{0}" WHERE chromosome_id = {chr_id};
                ALTER TABLE "{0}_{chr_id}" 
                    RENAME COLUMN "transcription_start" TO "start";
                ALTER TABLE "{0}_{chr_id}" 
                    RENAME COLUMN "transcription_end" TO "end";
                ALTER TABLE "{0}_{chr_id}" 
                    ADD COLUMN "refseq" bool DEFAULT true;
                    """.format(SequenceTranscriptionRegion._meta.db_table,
                               chr_id=chr_id)
    execute_query(q)

    try:
        print('Adding data...')
        path = os.path.join(get_vespucci_path(), 'atlas/pipeline/scripts')
        print(subprocess.check_output(path +
                    '/set_up_database.sh -g {0} -c refseq --prep'.format(
                                                    current_settings.GENOME),
                                      shell=True))
        print(subprocess.check_output(
                    path + '/transcripts_from_tags.sh -g {0} -c refseq '.format(
                                                    current_settings.GENOME)
                      + ' --schema_name=genome_reference_{0} '.format(
                                                    current_settings.GENOME)
                      + ' --tag_table=sequence_transcription_region '
                      + ' --stitch --stitch_processes=2 --set_density '
                      + ' --no_extended_gaps'
                      , shell=True))

    except Exception, e:
        print(e)
    finally:
        print('Deleting tables...')
        q = ''
        for chr_id in chr_ids:
            q += """DROP TABLE "{0}_{chr_id}";
                        """.format(SequenceTranscriptionRegion._meta.db_table,
                                   chr_id=chr_id)
        execute_query(q)
