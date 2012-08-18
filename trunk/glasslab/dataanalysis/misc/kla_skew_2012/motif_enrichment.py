'''
Created on Jul 4, 2012

@author: karmel

'''
from __future__ import division
from glasslab.dataanalysis.misc.gr_project_2012.elongation import get_rep_string
import sys
from glasslab.dataanalysis.motifs.motif_analyzer import MotifAnalyzer
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher


if __name__ == '__main__':
    yzer = MotifAnalyzer()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/KLA skew/'
    dirpath = yzer.get_path(dirpath)
    
    grouped = yzer.import_file(yzer.get_filename(dirpath, 'feature_vectors.txt'))
    
    repressed = []
    if True:
        # Can we predict pausing ratio?
        
        # Minimal ratio in KLA+Dex vs. KLA pausing
        try: min_ratio= float(sys.argv[1])
        except IndexError: min_ratio = -1
        try: thresh = int(sys.argv[3])
        except IndexError: thresh = 4
        
        grouped['relevant_sets'] = 0
        
        rep_ids = (1, 2, 3, 4)
        for replicate_id in rep_ids:
            rep_str = get_rep_string(replicate_id)
            
            
            primary_min = grouped['kla_{0}gene_body_lfc'.format(rep_str)] <= min_ratio
            
            repressed_set = grouped.ix[primary_min]['glass_transcript_id'].values.tolist()
            grouped['relevant_sets'] += primary_min.apply(int)
            
            repressed.append(repressed_set)
            
            print 'Genes with rep {0} KLA LFC <= {1}:'.format(
                                    rep_str, min_ratio), len(repressed_set)
            
            
        
        
        print 'Repressed in at least 4 reps:', sum(grouped['relevant_sets'] >= 4)
        print 'Repressed in at least 3 reps:', sum(grouped['relevant_sets'] >= 3)
        print 'Repressed in at least 2 reps:', sum(grouped['relevant_sets'] >= 2)
        print 'Repressed in at least 1 reps:', sum(grouped['relevant_sets'] >= 1)
        
        
        # For motif finding
        utrs = yzer.import_file(yzer.get_filename(dirpath, 'utr_regions.txt'))
        utrs['length_5_utr'] = (utrs['utr_start'] - utrs['utr_end']).apply(abs)
        
        for search_space in (200,600):
            yy1_positions = yzer.import_file(
                            yzer.get_filename(dirpath, 'position_file_yy1_{0}.txt'.format(search_space)))
            acceptor_positions = yzer.import_file(
                            yzer.get_filename(dirpath, 'position_file_acceptor_{0}.txt'.format(search_space)))
            
            
            
            
            ids = grouped[grouped['relevant_sets'] >= thresh]['glass_transcript_id']
            
            repr_data   = yy1_positions[yy1_positions['PositionID'].isin(ids)]
            all_data    = yy1_positions[yy1_positions['PositionID'].isin(grouped['glass_transcript_id'])]
            
            repr_utrs = utrs[utrs['glass_transcript_id'].isin(repr_data['PositionID'])]
            all_utrs = utrs[utrs['glass_transcript_id'].isin(all_data['PositionID'])]
            
            print 'Total transcripts:', len(grouped) 
            print 'Fraction with YY1 in {0} in total transcripts:'.format(search_space), len(all_data)/len(grouped) 
            print 'Fraction with YY1 in {0} in repressed transcripts:'.format(search_space), len(repr_data)/len(ids) 
            
            if True:
                grapher = SeqGrapher()
                grapher.boxplot([all_utrs['length_5_utr'], repr_utrs['length_5_utr']], 
                                ['All Genes', 'LFC in KLA <= {0}'.format(min_ratio)], 
                                title="Length of 5'UTR according to KLA response", 
                                xlabel='Gene Set', ylabel='Length in bp', show_outliers=False, show_plot=True)
                
                