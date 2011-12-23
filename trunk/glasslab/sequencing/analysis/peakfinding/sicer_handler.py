'''
Created on Jan 7, 2011

@author: karmel

SICER is a peak finder optimized for histone marks and similar diffuse,
island-like regions, rather than focal peaks like those created by
transcription factors.

For more information:
SICER (Statistical approach for the Identification of ChIP-Enriched Regions)
For details on the algorithm, please see 

A clustering approach for identification of enriched domains from
histone modification ChIP-Seq data,
Chongzhi Zang, Dustin E. Schones, Chen Zeng, Kairong Cui, Keji Zhao,
and Weiqun Peng, Bioinformatics (2009)

http://bioinformatics.oxfordjournals.org/content/25/15/1952.abstract

The functions and defaults here are adapted from SICER.sh
and SICER-rb.sh, which are included with the downloaded software.

Changes made to original software:
    
    * lib and src moved under single parent directory, sicer
    * __init__.py files added in sicer, lib, and src
    * run-make-graph-file-by-chrom.py renamed to run_make_graph_file_by_chrom.py
    * all module import statements modified to refer to full "import sicer.lib.UCSC", etc,
    rather than just "import UCSC"

'''
import os

from glasslab.config import current_settings
from sicer.src import remove_redundant_reads, run_make_graph_file_by_chrom,\
    find_islands_in_pr, associate_tags_with_chip_and_control_w_fc_q,\
    filter_islands_by_significance

THRESHOLD = 1
FRAGMENT_SIZE = 150
EFFECTIVE_GENOME = {'hg18': '.74',
                    'mm9': '.70' } # From MACS estimates

class SicerHandler(object):
    def process_bed_sample(self, output_dir, file_name, sample_file, 
                           window_size=200, gap_size=400, evalue=100, fdr=.001):
        
        current_dir = os.path.dirname(__file__)
        filtered_sample = self.remove_multiple_identical_tags(output_dir, file_name, 
                                                       input_file=sample_file, control=False)
        graph_file = self.run_make_graph_file_by_chrom(output_dir, file_name, filtered_sample, window_size)
        island_file= self.find_islands_in_pr(output_dir, file_name, graph_file, window_size, gap_size, evalue)
        differential_island_file = self.associate_tags_with_chip_and_control_w_fc_q(output_dir, file_name, 
                                                            os.path.join(current_dir,'data_files/control.bed'), 
                                                            filtered_sample, island_file)
        return self.find_significant_islands(output_dir, file_name, differential_island_file, fdr)
        
    def process_bed_sample_with_control(self, output_dir, file_name, sample_file, control_file, 
                                        window_size=200, gap_size=400, evalue=100, fdr='1E-3'):
        filtered_control = self.remove_multiple_identical_tags(output_dir, file_name, 
                                                              input_file=sample_file, control=False)
        filtered_sample = self.remove_multiple_identical_tags(output_dir, file_name, 
                                                              input_file=control_file, control=True)
        graph_file = self.run_make_graph_file_by_chrom(output_dir, file_name, filtered_sample, window_size)
        island_file = self.find_islands_in_pr(output_dir, file_name, 
                                              graph_file, window_size, gap_size, evalue)
        differential_island_file = self.associate_tags_with_chip_and_control_w_fc_q(output_dir, file_name, 
                                                            filtered_control, filtered_sample, island_file)
        return self.find_significant_islands(output_dir, file_name, differential_island_file, fdr)
        
    def remove_multiple_identical_tags(self, output_dir, file_name, input_file, control=False):
        '''
        Preprocess the raw $SAMPLE file to remove redundancy with threshold $CHIPTHRESHOLD
        '''
        output_file = os.path.join(output_dir, '%s_filtered_%s.bed' 
                                    % (file_name, control and 'control' or 'sample'))
        args = ['-s','%s' % current_settings.GENOME,
                '-b','%s' % input_file,
                '-t','%d' % THRESHOLD,
                '-o','%s' % output_file,
                '--output_dir','%s' % output_dir]
          
        remove_redundant_reads.main(args)
        return output_file
        
    def run_make_graph_file_by_chrom(self, output_dir, file_name, input_file, window_size=200):
        '''
        Partion the genome in windows and Generate summary files
        '''
        output_file = os.path.join(output_dir, '%s_summary.graph' % file_name)
        args = ['-s','%s' % current_settings.GENOME,
                '-b','%s' % input_file,
                '-w','%d' % window_size,
                '-i','%d' % FRAGMENT_SIZE,
                '-o','%s' % output_file,
                '--output_dir','%s' % output_dir]
          
        run_make_graph_file_by_chrom.main(args)
        return output_file
        
    def find_islands_in_pr(self, output_dir, file_name, input_file, window_size=200, gap_size=400, evalue=100):
        '''
        Find candidate islands exhibiting clustering
        '''
        output_file = os.path.join(output_dir, '%s_scored.probscoreisland' % file_name)
        args = ['-s','%s' % current_settings.GENOME,
                '-b','%s' % input_file,
                '-w','%d' % window_size,
                '-g','%d' % gap_size,
                '-t','%s' % EFFECTIVE_GENOME[current_settings.GENOME],
                '-e','%d' % evalue,
                '-f','%s' % output_file]
          
        find_islands_in_pr.main(args)
        return output_file
        
    def associate_tags_with_chip_and_control_w_fc_q(self, output_dir, file_name, control_file, sample_file, island_file):
        '''
        Find candidate islands exhibiting clustering
        '''
        output_file = os.path.join(output_dir, '%s_islands_summary_control' % file_name)
        args = ['-s','%s' % current_settings.GENOME,
                '-a','%s' % sample_file,
                '-b','%s' % control_file,
                '-d','%s' % island_file,
                '-f','%d' % FRAGMENT_SIZE,
                '-t','%s' % EFFECTIVE_GENOME[current_settings.GENOME],
                '-o','%s' % output_file,
                '--output_dir','%s' % output_dir]
          
        associate_tags_with_chip_and_control_w_fc_q.main(args)
        return output_file
        
    def find_significant_islands(self, output_dir, file_name, island_file, fdr=.001, p_value=None):
        '''
        Identify significant islands using FDR criterion
        '''
        output_file = os.path.join(output_dir, '%s_islands_summary_fdr' % file_name)
        args = ['-i','%s' % island_file,
                '-q','%s' % str(fdr or -1),
                '-p','%s' % str(p_value or -1),
                '-o','%s' % output_file]
          
        filter_islands_by_significance.main(args)
        return output_file
    
if __name__ == '__main__':
    handler = SicerHandler()
    handler.process_bed_sample('/Volumes/Unknowme/kallison/Sequencing/ChIPSeq/ThioMac/2010_04_13_Nathan/wt_KLA_1h_H4K12ac/output/sicer', 'wt_kla_1h_h4k12ac_04_10', '') 
    