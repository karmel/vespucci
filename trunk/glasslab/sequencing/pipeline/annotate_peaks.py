#!/bin/bash
'''
Created on Sep 24, 2010

@author: karmel

A script capable of reading in a fastq file, mapping with bowtie,
finding peaks with MACs, and annotating peaks.

Run from the command line like so:
python annotate_peaks.py <source.fastq> <output_dir>

'''
import os
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
import subprocess
import traceback
from datetime import datetime
from random import randint
from glasslab.sequencing.datatypes.peak import CurrentPeak
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.config.django_settings import DATABASES
from glasslab.utils.datatypes.genome_reference import SequenceIdentifier,\
    TranscriptionStartSite, GeneDetail, Genome
from glasslab.sequencing.datatypes.geneontology import GoSeqEnrichedTerm
from glasslab.utils.geneannotation.geneontology import GOAccessor

class FastqOptionParser(GlassOptionParser):
    options = [
               make_option('-f', '--file_path',action='store', type='string', dest='file_path', 
                           help='Path to FASTQ file for processing.'),
               make_option('-o', '--output_dir',action='store', type='string', dest='output_dir'),
               make_option('-c', '--control',action='store', type='string', dest='control',
                           help='BOWTIE file path to be used for MACS peak finding controls.'),
               make_option('-g', '--genome',action='store', type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm8, mm8r, mm9, hg18, hg18r'),
               make_option('--project_name',action='store', type='string', dest='project_name',  
                           help='Optional name to be used as file prefix for created files.'),
               make_option('--delete_tables',action='store_true', dest='delete_tables', default=False, 
                           help='Delete peak tables after run.'),
               make_option('--skip_bowtie',action='store_true', dest='skip_bowtie', default=False, 
                           help='Skip bowtie; presume MACS uses input file directly.'),
               make_option('--skip_macs',action='store_true', dest='skip_macs', default=False, 
                           help='Skip MACS; presume peak annotation uses input file directly.'),
               make_option('--peak_table',action='store', dest='peak_table',
                           help='Skip saving and annotating peaks; peak table will be used directly.'),
               ]
    
def check_input(options):
    '''
    Check that required arguments and directories are in place.
    '''
    if not options.file_path:
        raise Exception('Please make sure you have supplied an input FASTQ file and an output directory.')
    if not os.path.exists(options.file_path):
        raise Exception('Sorry, but the specified input file cannot be found: %s' % os.path.realpath(options.file_path))
    
    if not os.path.exists(options.output_dir):
        os.mkdir(options.output_dir)
        print 'Creating output directory %s' % options.output_dir
    
    # Get a file name prefix for use with generated files, using FASTQ as base
    file_name = options.project_name or '.'.join(os.path.basename(options.file_path).split('.')[:-1])
    
    return file_name

def call_bowtie(options, file_name):
    bowtie_output = file_name + '_bowtie.map'
    bowtie_file_path = os.path.join(options.output_dir, bowtie_output)
    bowtie_command = 'bowtie %s %s %s' % (options.genome, options.file_path, bowtie_file_path)
    try: subprocess.check_call(bowtie_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to process FASTQ file with bowtie. Traceback:\n%s'
                                % traceback.format_exc())
    return bowtie_file_path

def call_macs(options, file_name, bowtie_file_path):
    # Note that MACS does not allow output file specification; cd inline to force output into directory
    macs_command = 'cd %s && macs -t %s -n %s -g %s -f BOWTIE' % (options.output_dir,
                                                                  bowtie_file_path, file_name, 
                                                                  'hs' and options.genome[:2] == 'hg' or 'mm')
    if options.control: macs_command += ' -c %s' & options.control
    
    try: subprocess.check_call(macs_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to process bowtie file with MACS. Traceback:\n%s'
                                % traceback.format_exc())
    return os.path.join(options.output_dir, '%s_peaks.xls' % file_name)

def import_peaks(options, file_name, macs_file_path):
    '''
    Given a MACS peak file, save a temp table and store peak data.
    '''
    table_name = '%s_%s_%s' % (file_name.replace(' ','_'), 
                            datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                            str(randint(0,999999)))
    
    CurrentPeak.create_table(table_name)
    data = DelimitedFileParser(macs_file_path).get_array()
    for row in data:
        if row[0] == 'chr': continue
        peak = CurrentPeak.init_from_macs_row(row)
        peak.save()
    
def annotate_peaks(options):
    '''
    Now that we have our peaks saved, find the nearest TSS and chromosome loc annotations.
    '''
    CurrentPeak.find_transcriptions_start_sites(genome=options.genome)
    CurrentPeak.find_chromosome_location_annotation(genome=options.genome)
    
def get_goseq_annotation(options, file_name):
    '''
    Our peaks have all been saved and annotated; get enriched GO terms from GOSeq.
    
    To run::
    
        r /Path/to/R/script.r db_host db_port db_name db_user db_pass 
                gene_detail_table seq_table tss_table genome_table current_peaks_table 
                genome output_dir file_name
    
    Creates and saves plot of Probability Weighting Function, and
    creates a table that has GO term IDs and enrichment p-values.
    '''
    import glasslab.sequencing.goseq as goseq
    r_script_path = os.path.join(os.path.dirname(goseq.__file__),'ontology_for_peaks.r')
    goseq_command = '%s "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (r_script_path,
                                                         DATABASES['default']['HOST'],
                                                         DATABASES['default']['PORT'],
                                                         DATABASES['default']['NAME'],
                                                         DATABASES['default']['USER'],
                                                         DATABASES['default']['PASSWORD'],
                                                         GeneDetail._meta.db_table.replace('"','\\"'),
                                                         SequenceIdentifier._meta.db_table.replace('"','\\"'),
                                                         TranscriptionStartSite._meta.db_table.replace('"','\\"'),
                                                         Genome._meta.db_table.replace('"','\\"'),
                                                         CurrentPeak._meta.db_table.replace('"','\\"'),
                                                         options.genome, 
                                                         options.output_dir, file_name
                                                         )
    try: subprocess.check_call(goseq_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to get GOSeq analysis. Traceback:\n%s'
                                % traceback.format_exc())
def output_goseq_enriched_ontology(options, file_name):
    '''
    For saved GoSeq term ids, output file of term id, term, and p val 
    for all terms with p val <= .05
    '''
    GoSeqEnrichedTerm.set_table_name(CurrentPeak._meta.db_table)
    # Get list of (term id, p val) tuples
    enriched = GoSeqEnrichedTerm.objects.filter(p_value_overexpressed__lte=.05
                                    ).values_list('go_term_id','p_value_overexpressed')
    term_ids, p_vals = zip(*enriched)
    # Get corresponding terms for human readability
    term_names_by_id = dict(GOAccessor().get_terms_for_ids(list(term_ids)))
    term_rows = zip(term_ids, [term_names_by_id[id] for id in term_ids], p_vals)
    # Output tsv
    header = 'GO Term ID\tGO Term\tP-value of overexpression\n'
    output_tsv = header + '\n'.join(['\t'.join([str(field) for field in row]) for row in term_rows])
    file_path = os.path.join(options.output_dir,'%s_GOSeq_enriched_terms.tsv' % file_name)
    file = open(file_path, 'w')
    file.write(output_tsv)

if __name__ == '__main__':
    run_from_command_line = True # Useful for debugging in Eclipse
    
    parser = FastqOptionParser()
    options, args = parser.parse_args()
    
    # Allow for easy running from Eclipse
    if not run_from_command_line:
        options.file_path = '/Users/karmel/GlassLab/SourceData/ThioMac_Lazar/test'
        options.output_dir = 'first_test'
        options.peak_table = 'enriched_peaks_enriched_peaks_first_test_2010-09-30_16-04-52_454502'
    
    file_name = check_input(options)
    
    
    if not options.skip_bowtie:
        print 'Processing FASTQ file using bowtie.'
        bowtie_file_path = call_bowtie(options, file_name)
    else:
        print 'Skipping bowtie.'
        bowtie_file_path = options.file_path
    
    if not options.skip_macs:
        print 'Processing bowtie file using MACS'
        macs_file_path = call_macs(options, file_name, bowtie_file_path)
    else:
        print 'Skipping macs.'
        macs_file_path = bowtie_file_path
    
    if not options.peak_table:
        print 'Saving peaks to table.'
        import_peaks(options, file_name, macs_file_path)

        print 'Annotating peaks.'
        annotate_peaks(options)
    else:
        CurrentPeak.set_table_name(options.peak_table)
        print 'Using existing peaks table "%s"' % CurrentPeak._meta.db_table 
        
    print 'Analyzing with GOSeq.'
    get_goseq_annotation(options, file_name)
    output_goseq_enriched_ontology(options, file_name)
    