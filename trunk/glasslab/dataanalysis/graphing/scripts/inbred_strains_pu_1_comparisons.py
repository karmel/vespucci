'''
Created on Mar 23, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import os
from scipy.stats.stats import ttest_ind

if __name__ == '__main__':
    grapher = SeqGrapher()
    
    dirpath = '/Volumes/karmel/Desktop/Projects/GlassLab/Notes_and_Reports/Inbred strains/Peak comparisons/Compared with NOD/'
    filename = os.path.join(dirpath, 'bl6_gt_balb_with_nod_pu_1_unique.txt')
    data = grapher.import_file(filename)
    
    data = data.fillna(0) # For easy log graphing
    
    wt_peaks, balb_peaks, nod_peaks, balb2_peaks = 67074, 79353, 107716, 94199
    
    data = grapher.normalize(data, 'balb_pu_1_tag_count', balb_peaks/wt_peaks)
    data = grapher.normalize(data, 'nod_pu_1_tag_count', nod_peaks/wt_peaks)
    data = grapher.normalize(data, 'balb2_pu_1_tag_count', balb2_peaks/wt_peaks)
    
    data['wt_to_balb'] = data['wt_pu_1_tag_count']/data['balb_pu_1_tag_count']
    data['nod_to_balb'] = data['nod_pu_1_tag_count']/data['balb2_pu_1_tag_count']
    
    data['nod_with_bl6'] = data['nod_sv_id'] <= .1
    nod_with_bl6 = data[data['nod_with_bl6'] == True]
    nod_with_balb = data[data['nod_with_bl6'] == False]
    if False:
        ax = grapher.scatterplot(nod_with_bl6, 'wt_pu_1_tag_count', 'nod_pu_1_tag_count',
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
        ax = grapher.scatterplot(nod_with_balb, 'wt_pu_1_tag_count', 'nod_pu_1_tag_count',
                            subplot=122, log=True, color='red', 
                            xlabel='C57Bl6 PU.1 tag counts', ylabel='NOD PU.1 tag counts',
                            title='C57Bl6 vs. NOD PU.1 peaks\nwhere C57Bl6 has a PU.1 motif and BALBc does not', 
                            label='NOD SNP == BALBc SNP', 
                            add_noise=False,
                            show_2x_range=False, show_legend=True, text_color=True, 
                            show_count=True, show_correlation=True, show_plot=False, ax=ax)
        #ax.set_ylim(4,128)
        grapher.save_plot(os.path.join(dirpath, 'bl6_vs_nod_pu_1_peak_tag_counts_bl6_gt_balb_unique.png'))
        grapher.show_plot()
    
        # Boxplots: avg PU.1 in Bl6 for whole set; avg PU.1 in BALB for whole set; 
        # avg PU.1 for NOD in whole set; avg PU.1 in NOD set with Bl6; avg PU.1 in NOD set with BALB
        
        ax = grapher.boxplot([data['wt_pu_1_tag_count'],data['balb_pu_1_tag_count_norm'],data['nod_pu_1_tag_count_norm'],
                              nod_with_bl6['nod_pu_1_tag_count_norm'],nod_with_balb['nod_pu_1_tag_count_norm']], 
                                  bar_names=['C57Bl6 Peaks', 'BALBc Peaks', 'NOD Peaks', 
                                             'NOD Peaks\nwhere\nNOD == C57Bl6', 'NOD Peaks\nwhere\nNOD == BALBc',],
                                  title='PU.1 peak tags where BALBc has a SNP that ruins its PU.1 Motif', 
                                  xlabel='', ylabel='Tags per PU.1 peak', 
                                  show_outliers=False, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'peak_boxplots_no_balb_motif_norm_by_tot_peaks.png'))
        grapher.show_plot()
        
    print 'p-val that BALBc is different than C57Bl6: %g' % ttest_ind(data['wt_pu_1_tag_count'],data['balb_pu_1_tag_count_norm'])[1]
    print 'p-val that NOD (all) is different than C57Bl6: %g' % ttest_ind(data['wt_pu_1_tag_count'],data['nod_pu_1_tag_count_norm'])[1]
    print 'p-val that NOD == C57Bl6 is different than C57Bl6: %g' % ttest_ind(data['wt_pu_1_tag_count'],nod_with_bl6['nod_pu_1_tag_count_norm'])[1]
    print 'p-val that NOD == BALBc is different than C57Bl6: %g' % ttest_ind(data['wt_pu_1_tag_count'],nod_with_balb['nod_pu_1_tag_count_norm'])[1]