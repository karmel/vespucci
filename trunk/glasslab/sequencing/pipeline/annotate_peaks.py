#!/bin/bash
'''
Created on Sep 24, 2010

@author: karmel

A script capable of reading in a fastq file, mapping with bowtie,
finding peaks with MACs or diffuse regions with SICER, and annotating peaks.

Run from the command line.

'''
import os
from glasslab.utils.scripting import GlassOptionParser
from optparse import make_option
import subprocess
import traceback
from glasslab.sequencing.datatypes.peak import GlassPeak
from glasslab.utils.parsing.delimited import DelimitedFileParser
from glasslab.sequencing.pipeline.annotate_base import check_input, call_bowtie,\
    create_schema, _print, trim_sequences
from glasslab.sequencing.analysis.peakfinding.sicer_handler import SicerHandler

class FastqOptionParser(GlassOptionParser):
    options = [
               make_option('-f', '--file_path',action='store', type='string', dest='file_path', 
                           help='Path to FASTQ file for processing.'),
               make_option('-o', '--output_dir',action='store', type='string', dest='output_dir'),
               make_option('-c', '--control',action='store', type='string', dest='control',
                           help='BOWTIE file path to be used for MACS of SICER peak finding controls.'),
               make_option('-g', '--genome',action='store', type='string', dest='genome', default='mm9', 
                           help='Currently supported: mm8, mm8r, mm9, hg18, hg18r'),
               make_option('--project_name',action='store', type='string', dest='project_name',  
                           help='Optional name to be used as file prefix for created files.'),
            
               make_option('--schema_name',action='store', type='string', dest='schema_name',  
                           help='Optional name to be used as schema for created DB tables.'),
               
               make_option('--peak_type',action='store', dest='peak_type',  
                           help='What type of peak are we looking for? H4K3me1, PU_1, etc.? Should match a type in PeakType table.'),
                           
               make_option('--skip_bowtie',action='store_true', dest='skip_bowtie', default=False, 
                           help='Skip bowtie; presume MACS or SICER uses input file directly.'),
               make_option('--skip_trim',action='store_true', dest='skip_trim', default=False, 
                           help='Trim the sequences of polyA regions before sending to bowtie.'),
               make_option('--skip_bed',action='store_true', dest='skip_bed', default=False, 
                           help='Skip conversion to BED; presume SICER uses input file directly.'),
               make_option('--skip_peak_finding',action='store_true', dest='skip_peak_finding', default=False, 
                           help='Skip peak finding with MACS or SICER; presume peak annotation uses input file directly.'),
               make_option('--skip_table_upload',action='store_true', dest='skip_table_upload', default=False, 
                           help='Skip uploading peaks into a table.'),
               
               ]
    
def bowtie_to_bed(options, file_name, bowtie_file_path):
    bed_output = file_name + '_bowtie.bed'
    bed_file_path = os.path.join(options.output_dir, bed_output)
    
    bed_command = '''awk 'BEGIN {FS= "\t"; OFS="\t"} { print $3, $4, $4+length($5)-1, $1, "0", $2}' %s > %s ''' \
                        % (bowtie_file_path, bed_file_path)

    try: subprocess.check_call(bed_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to convert bowtie file into BED file. Traceback:\n%s'
                                % traceback.format_exc())
    return bed_file_path

def call_macs(options, file_name, bowtie_file_path):
    # Note that MACS does not allow output file specification; cd inline to force output into directory
    macs_command = 'cd %s && macs -t %s -n %s -g %s -f BOWTIE' % (options.output_dir,
                                                                  bowtie_file_path, file_name, 
                                                                  'hs' and options.genome[:2] == 'hg' or 'mm')
    if options.control: macs_command += ' -c %s' % options.control
    
    try: subprocess.check_call(macs_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to process bowtie file with MACS. Traceback:\n%s'
                                % traceback.format_exc())
    return os.path.join(options.output_dir, '%s_peaks.xls' % file_name)

def call_sicer(options, file_name, bed_file_path):
    output_dir = os.path.join(options.output_dir, 'sicer')
    if not os.path.exists(output_dir): os.mkdir(output_dir)
    try: 
        sicer = SicerHandler()
        if not options.control:
            sicer_output = sicer.process_bed_sample(output_dir, file_name, bed_file_path)
        else:
            sicer_output = sicer.process_bed_sample_with_control(output_dir, file_name, bed_file_path, options.control)
            
    except Exception:
        raise Exception('Exception encountered while trying to process BED file with SICER. Traceback:\n%s'
                                % traceback.format_exc())
    return sicer_output

def import_peaks(options, file_name, peaks_file_path, peak_type):
    '''
    Given a MACS peak file, save a temp table and store peak data.
    '''
    GlassPeak.create_table(file_name)
    
    data = DelimitedFileParser(peaks_file_path).get_array()
    if data[0][0] == 'chr':
        data = data[1:] # Header row
    for row in data:
        if not peak_type.diffuse:
            peak = GlassPeak.init_from_macs_row(row)
        else:
            peak = GlassPeak.init_from_sicer_row(row)
        peak.save()
    
    GlassPeak.add_indices()
    GlassPeak.add_record_of_tags(peak_type=peak_type)
    
def annotate_peaks(options):
    '''
    Now that we have our peaks saved, find the nearest TSS and chromosome loc annotations.
    '''
    #GlassPeak.find_transcriptions_start_sites(genome=options.genome)
    #GlassPeak.find_chromosome_location_annotation(genome=options.genome)

def output_peak_annotation(options, file_name):   
    # Output full annotation set to file
    peaks = GlassPeak.objects.order_by('chromosome','start','end')
    peak_output = []
    for peak in peaks:
        # Prep promoter fields, if available
        try: 
            promoter = peak.transcription_start_site.sequence_identifier
            gene_details = [promoter.sequence_identifier]
        except Exception: 
            promoter = None
            gene_details = ['']
        try:
            detail = promoter.gene_detail
            gene_details += [detail.refseq_gene_id, detail.unigene_identifier,
                             detail.ensembl_identifier, detail.gene_name,
                             detail.gene_alias, detail.gene_description]
        except Exception: gene_details += ['']*6
        
        # Prep chromosome location annotation fields, if available
        try:
            chr = peak.chromosome_location_annotation
            chr_details = [chr.type, chr.description]
        except Exception: chr_details = ['Intergenic','Nonspecific']
        
        fields = [peak.id, peak.chromosome, peak.start, peak.end,
                  peak.length, peak.summit, peak.tag_count,
                  peak.log_ten_p_value, peak.fold_enrichment,
                  peak.distance] + chr_details + gene_details
        
        peak_output.append(map(lambda x: str(x).strip(), fields))
    header = 'Peak ID\tChromosome\tStart\tEnd\tLength\tSummit\tTag Count\tlog10(p-value)\tFold Enrichment\tDistance to TSS'
    header += '\tLocation Annotation\tLocation Annotation Description'
    header += '\tNearest Promoter\tRefSeq ID\tUnigene\tEnsembl\tGene Name\tGene Alias\tGene Description'
    output_tsv = header + '\n' + '\n'.join(['\t'.join(row) for row in peak_output])
    file_path = os.path.join(options.output_dir,'%s_gene_annotation.tsv' % file_name)
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
        _print('Processing FASTQ file using bowtie.')
        if not options.skip_trim:
            trim_sequences(options, file_name)
        bowtie_file_path = call_bowtie(options, file_name, suppress_columns=False)
    else:
        _print('Skipping bowtie.')
        bowtie_file_path = options.file_path
    
    if not options.skip_peak_finding: 
        peak_type = GlassPeak.peak_type(options.peak_type or options.project_name)
        if not peak_type: 
            raise Exception('Could not find appropriate PeakType record for peak type %s' % 
                                          (options.peak_type or options.project_name))
        if not peak_type.diffuse:
            _print('Processing bowtie file using MACS')
            peaks_file_path = call_macs(options, file_name, bowtie_file_path)
        else:
            if not options.skip_bed:
                _print('Converting bowtie file to BED')
                bed_file_path = bowtie_to_bed(options, file_name, bowtie_file_path)
            else: bed_file_path = bowtie_file_path
            _print('Processing BED file using SICER')
            peaks_file_path = call_sicer(options, file_name, bed_file_path)
    else:
        _print('Skipping peak finding.')
        peaks_file_path = bowtie_file_path
    
    if not options.skip_table_upload:
        peak_type = GlassPeak.peak_type(options.peak_type or options.project_name)
        _print('Creating schema if necessary.')
        create_schema()
        _print('Saving peaks to table.')
        import_peaks(options, file_name, peaks_file_path, peak_type)
