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
    
    loc = '/Users'
    dirpath = '/karmel/Desktop/Projects/GlassLab/Notes_and_Reports/Inbred strains/Groseq comparisons/'
    if not os.path.exists(loc + dirpath):
        loc = '/Volumes'
    dirpath = loc + dirpath
    
    filename = os.path.join(dirpath, 'groseq_with_h3k4me2.txt')
    data = grapher.import_file(filename)
    
    data = data.fillna(0) 
    
    nod_norm, balb_norm = 0.393529, 0.359488
    nod_to_balb_norm = 1.102844
    
    data = grapher.normalize(data, 'balb_tag_count', nod_norm)
    data = grapher.normalize(data, 'nod_tag_count', balb_norm)
    
    
    print len(data)
    
    data['nod_with_bl6'] = data['nod_sv_id'] <= .1
    
    nod_with_bl6 = data[data['nod_with_bl6'] == True]
    nod_with_balb = data[data['nod_with_bl6'] == False]
    
    nod_with_bl6 = grapher.collapse_strands(nod_with_bl6)
    nod_with_balb = grapher.collapse_strands(nod_with_balb)
    nod_with_bl6 = nod_with_bl6[nod_with_bl6['wt_peak_tag_count'] > 2*nod_with_bl6['balb_peak_tag_count']]
    nod_with_balb = nod_with_balb[nod_with_balb['wt_peak_tag_count'] > 2*nod_with_balb['balb_peak_tag_count']]
    print len(nod_with_bl6), len(nod_with_balb)
    if False:
        ax = grapher.scatterplot(nod_with_bl6, 'balb_tag_count', 'nod_tag_count_norm',
                            subplot=121, log=True, color='blue', 
                            xlabel='BALBc tag counts', ylabel='NOD tag counts',
                            title='BALBc vs. NOD GRO-seq tag counts\nwhere C57Bl6 has a PU.1 motif and BALBc does not', 
                            label='NOD SNP == C57Bl6 SNP',
                            add_noise=False,
                            show_2x_range=False, show_legend=True, 
                            show_count=True, show_correlation=True, text_shift=False, 
                            text_color=True, show_plot=False)
        #grapher.save_plot(os.path.join(dirpath, 'bl6_vs_nod_pu_1_peak_tag_counts_bl6_gt_balb_no_balb_motif_nod_eq_bl6.png'))
        #grapher.show_plot()
        ax = grapher.scatterplot(nod_with_balb, 'balb_tag_count', 'nod_tag_count_norm',
                            subplot=122, log=True, color='red', 
                            xlabel='BALBc tag counts', ylabel='NOD tag counts',
                            title='BALBc vs. NOD GRO-seq tag counts\nwhere C57Bl6 has a PU.1 motif and BALBc does not', 
                            label='NOD SNP == BALBc SNP', 
                            add_noise=False,
                            show_2x_range=False, show_legend=True, text_color=True, 
                            show_count=True, show_correlation=True, show_plot=False, ax=ax)
        #ax.set_ylim(4,128)
        grapher.save_plot(os.path.join(dirpath, 'balbc_vs_nod_pu_1_peak_tag_counts_bl6_gt_balb_unique.png'))
        grapher.show_plot()
    
    if True:
        # Boxplots
        
        ax = grapher.boxplot([data['wt_tag_count'], data['balb_tag_count_norm'],data['nod_tag_count_norm'],
                              nod_with_bl6['nod_tag_count_norm'],nod_with_balb['nod_tag_count_norm']], 
                                  bar_names=['C57Bl6 Tags','BALBc Tags', 'NOD Tags', 
                                             'NOD Tags\nwhere\nNOD == C57Bl6', 'NOD Tags\nwhere\nNOD == BALBc',],
                                  title='GRO-seq tags where BALBc has a SNP and half H3K4me2', 
                                  xlabel='', ylabel='Tags in transcript at H3K4me2 peak', 
                                  show_outliers=False, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'peak_boxplots_all_h3k4me2_collapsed.png'))
        grapher.show_plot()
    
    
    if True:
        print 'p-val that BALBc is different than C57Bl6: %g' % ttest_ind(data['wt_tag_count'],data['balb_tag_count_norm'])[1]
        print 'p-val that NOD (all) is different than C57Bl6: %g' % ttest_ind(data['wt_tag_count'],data['nod_tag_count_norm'])[1]
        print 'p-val that NOD == C57Bl6 is different than C57Bl6: %g' % ttest_ind(data['wt_tag_count'],nod_with_bl6['nod_tag_count_norm'])[1]
        print 'p-val that NOD == BALBc is different than C57Bl6: %g' % ttest_ind(data['wt_tag_count'],nod_with_balb['nod_tag_count_norm'])[1]
        
        print 'p-val that NOD (all) is different than BALBc: %g' % ttest_ind(data['balb_tag_count_norm'],data['nod_tag_count_norm'])[1]
        print 'p-val that NOD == C57Bl6 is different than BALBc: %g' % ttest_ind(data['balb_tag_count_norm'],nod_with_bl6['nod_tag_count_norm'])[1]
        print 'p-val that NOD == BALBc is different than BALBc: %g' % ttest_ind(data['balb_tag_count_norm'],nod_with_balb['nod_tag_count_norm'])[1]