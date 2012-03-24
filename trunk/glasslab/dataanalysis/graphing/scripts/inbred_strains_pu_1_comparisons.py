'''
Created on Mar 23, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import os

if __name__ == '__main__':
    grapher = SeqGrapher()
    
    dirpath = '/Users/karmel/GlassLab/Notes_and_Reports/Inbred strains/Peak comparisons/Compared with NOD/'
    filename = os.path.join(dirpath, 'bl6_gt_balb_with_nod_pu_1_snps_no_balb_motif.txt')
    data = grapher.import_file(filename)
    
    data = data.fillna(.1) # For easy log graphing
    
    # notx
    wt_total_tags, balb_total_tags, nod_total_tags, balb2_total_tags = 67074, 79353, 107716, 94199
    # KLA
    #wt_total_tags, balb_total_tags, nod_total_tags, balb2_total_tags = 69318, 77117, 84410, 126066
    
    data = grapher.normalize(data, 'balb_pu_1_tag_count', (wt_total_tags/balb_total_tags))
    data = grapher.normalize(data, 'nod_pu_1_tag_count', (wt_total_tags/nod_total_tags))
    data = grapher.normalize(data, 'balb2_pu_1_tag_count', (wt_total_tags/balb2_total_tags))
    
    data['wt_to_balb'] = data['wt_pu_1_tag_count']/data['balb_pu_1_tag_count_norm']
    data['nod_to_balb'] = data['nod_pu_1_tag_count']/data['balb2_pu_1_tag_count_norm']
    
    nod_with_balb = data[data['nod_sv_id'] > .1]
    nod_with_bl6 = data[data['nod_sv_id'] <= .1]
    
    ax = grapher.scatterplot(nod_with_bl6, 'wt_pu_1_tag_count', 'nod_pu_1_tag_count_norm',
                        subplot=121, log=True, color='blue', 
                        xlabel='C57Bl6 PU.1 tag counts', ylabel='NOD PU.1 tag counts',
                        title='C57Bl6 vs. NOD PU.1 peaks\nwhere C57Bl6 has a PU.1 motif and BALBc does not', 
                        label='NOD SNP == C57Bl6 SNP',
                        add_noise=False,
                        show_2x_range=False, show_legend=True, 
                        show_count=True, show_correlation=True, text_shift=False, 
                        text_color=True, show_plot=False)
    #grapher.save_plot(os.path.join(dirpath, 'bl6_vs_nod_pu_1_peak_tag_counts_bl6_gt_balb_no_balb_motif_nod_eq_bl6.png'))
    #grapher.show_plot()
    ax = grapher.scatterplot(nod_with_balb, 'wt_pu_1_tag_count', 'nod_pu_1_tag_count_norm',
                        subplot=122, log=True, color='red', 
                        xlabel='C57Bl6 PU.1 tag counts', ylabel='NOD PU.1 tag counts',
                        title='C57Bl6 vs. NOD PU.1 peaks\nwhere C57Bl6 has a PU.1 motif and BALBc does not', 
                        label='NOD SNP == BALBc SNP', 
                        add_noise=False,
                        show_2x_range=False, show_legend=True, text_color=True, 
                        show_count=True, show_correlation=True, show_plot=False, ax=ax)
    #ax.set_ylim(4,128)
    grapher.save_plot(os.path.join(dirpath, 'bl6_vs_nod_pu_1_peak_tag_counts_bl6_gt_balb_no_balb_motif_nod_eq_balb.png'))
    grapher.show_plot()
    