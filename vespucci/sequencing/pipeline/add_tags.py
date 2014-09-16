'''
Created on Oct 18, 2010

@author: karmel

A script capable of reading in a SAM, BAM, or 6-column Bowtie file, 
loading tags into a table, and creating necessary AtlasTag records.

Run from the command line like so:
python annotate_peaks.py -f <source.fastq> -o <output_dir> --project_name=my_project

'''
from __future__ import division

from multiprocessing import Pool
from optparse import make_option
import os
import shutil
import subprocess
import traceback

from django.db import connection, transaction
from vespucci.config import current_settings
from vespucci.sequencing.pipeline.add_short_reads import check_input, _print, \
    create_schema
from vespucci.utils.convert_for_upload import TagFileConverter
from vespucci.utils.database import execute_query_without_transaction
from vespucci.utils.scripting import VespucciOptionParser


class FastqOptionParser(VespucciOptionParser):
    options = [
        make_option('-g', '--genome', action='store',
                    type='string', dest='genome', default='mm9',
                    help='Currently supported: mm9, dm3'),
        make_option('-c', '--cell_type', action='store',
                    type='string', dest='cell_type',
                    help='Cell type for this run?'),
        make_option('-f', '--file_name', action='store',
                    type='string', dest='file_name',
                    help='Path to SAM, BAM, or Bowtie file for processing.'),
        make_option('-o', '--output_dir', action='store',
                    type='string', dest='output_dir'),
        make_option('-p', '--processes', action='store',
                    dest='processes', default=None,
                    help='How many processes can be used?'),
        make_option('--project_name', action='store',
                    type='string', dest='project_name',
                    help='Optional name to be used as file prefix for created files.'),

        make_option('--schema_name', action='store',
                    type='string', dest='schema_name',
                    help='Optional name to be used as schema for created DB tables.'),

        make_option('--input_file_type', action='store',
                    type='string', dest='input_file_type',
                    help='File type (bowtie, sam, bam, 4col) to be converted to 4 column input file. Will guess if not specified.'),

        make_option('--skip_file_conversion', action='store_true',
                    dest='skip_file_conversion', default=False,
                    help='Skip conversion to four column format. Uses file directly.'),
        make_option('--prep_table', action='store',
                    dest='prep_table',
                    help='Skip transferring tags from file to prep table; prep tag table will be used directly.'),
        make_option('--skip_tag_table', action='store_true',
                    dest='skip_tag_table',
                    help='Skip transferring tags to table; tag table will be used directly.'),

        make_option('--no_refseq_segmentation', action='store_true',
                    dest='no_refseq_segmentation',
                    help='Do not mark RefSeq tags as separate, preventing forced segmentation at RefSeq genes.'),

    ]


def split_tag_file(options, file_name, tag_file_path):
    '''
    Trying to upload a single file all at once into the table 
    often means we lose the DB connection. 
    Split the large file here to allow more manageable looping.
    '''
    output_dir = os.path.join(options.output_dir, 'split_tag_files')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    output_prefix = os.path.join(output_dir, '{}_'.format(file_name))
    split_command = 'split -a 4 -l 100000 {} {}'.format(tag_file_path,
                                                        output_prefix)
    try:
        subprocess.check_call(split_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying '
                        + 'to split tag file. Traceback:\n'
                        + traceback.format_exc())

    return output_dir


def copy_into_table_from_range(tag_split_dir, file_names):
    for f_name in file_names:
        _copy_into_table(tag_split_dir, f_name)


def _copy_into_table(tag_split_dir, f_name):
    full_path = os.path.join(tag_split_dir, f_name)
    tag_file = file(full_path)
    try:
        connection.close()
        cursor = connection.cursor()
        cursor.copy_expert("""COPY "{}" (strand_char, 
                            chromosome, 
                            "start", 
                            sequence_matched)
                            FROM STDIN WITH CSV DELIMITER E'\t';""".format(
            AtlasTag.prep_table),
            tag_file)
        transaction.commit_unless_managed()
    except Exception:
        _print('Encountered exception while trying to copy data:\n'
               + traceback.format_exc())
        raise


def upload_tag_files(options, file_name, tag_split_dir):
    AtlasTag.create_prep_table(file_name)

    file_names = os.listdir(tag_split_dir)
    processes = current_settings.ALLOWED_PROCESSES
    step_size = max(1, len(file_names) // processes)
    p = Pool(processes)
    for start in range(0, len(file_names), step_size):
        try:
            p.apply_async(copy_into_table_from_range,
                          args=(tag_split_dir,
                                file_names[start:(start + step_size)]))
        except Exception:
            raise Exception('Exception encountered while trying to upload '
                            + 'tag files to tables. Traceback:\n'
                            + traceback.format_exc())
    p.close()
    p.join()

    connection.close()
    shutil.rmtree(tag_split_dir)


def translate_prep_columns(file_name):
    '''
    Transfer prep tags to indexed, streamlined Atlas tags for annotation.
    '''
    # AtlasTag.set_table_name('tag_' + file_name)
    AtlasTag.create_parent_table(file_name)
    AtlasTag.create_partition_tables()
    AtlasTag.translate_from_prep()


def add_indices(set_refseq=True):
    # Execute after all the ends have been calculated,
    # as otherwise the insertion of ends takes far too long.
    AtlasTag.add_indices()
    execute_query_without_transaction('VACUUM ANALYZE "{}";'.format(
        AtlasTag._meta.db_table))
    if set_refseq:
        AtlasTag.set_refseq()
    AtlasTag.add_record_of_tags()

if __name__ == '__main__':
    parser = FastqOptionParser()
    options, args = parser.parse_args()

    file_name = check_input(options)
    parser.set_genome(options)
    cell_type, cell_base = parser.set_cell(options)

    if options.processes:
        current_settings.ALLOWED_PROCESSES = int(options.processes)

    from vespucci.sequencing.datatypes.tag import AtlasTag

    if not options.skip_tag_table:
        if not options.prep_table:
            # First, convert the mapped file to the desired format.
            converter = TagFileConverter()
            converted_file = converter.guess_file_type(options.file_name,
                                                       options.input_file_type)

            _print('Creating schema if necessary.')
            create_schema()
            _print('Uploading tag file into table.')
            tag_split_dir = split_tag_file(options, file_name, converted_file)
            upload_tag_files(options, file_name, tag_split_dir)

            # Remove 4column file to conserve space.
            os.remove(converted_file)
        else:
            _print('Skipping upload of tag rows into table.')
            AtlasTag.set_prep_table(options.prep_table)

        _print('Translating prep columns to integers.')
        translate_prep_columns(file_name)
        _print('Adding indices.')
        AtlasTag.set_table_name('tag_' + file_name)
        add_indices(set_refseq=(not options.no_refseq_segmentation))
        AtlasTag.delete_prep_table()

    else:
        _print('Skipping creation of tag table')
        AtlasTag.set_table_name('tag_' + file_name)
        if not options.no_refseq_segmentation:
            AtlasTag.set_refseq()
