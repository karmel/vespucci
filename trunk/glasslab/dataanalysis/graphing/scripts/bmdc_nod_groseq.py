'''
Created on Mar 23, 2012

@author: karmel
'''
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import os

if __name__ == '__main__':
    grapher = SeqGrapher()
    
    dirpath = '/Users/karmel/Desktop/Projects/GlassLab/Notes_and_Reports/NOD_BALBc/BMDCs/Analysis/'
    filename = os.path.join(dirpath, 'balbc_nod_vectors.txt')
    data = grapher.import_file(filename)
    
    # vs balbc counterpart
    data = grapher.normalize(data, 'nod_notx_0h_tag_count', 2.418341)
    data = grapher.normalize(data, 'diabetic_nod_notx_0h_tag_count', 1.065332)
    data = grapher.normalize(data, 'slow_diabetic_nod_notx_0h_tag_count', 0.345331)
    
    # Vs nod notx
    data = grapher.normalize(data, 'diabetic_nod_notx_0h_tag_count', 0.470096, suffix='_norm_2')
    data = grapher.normalize(data, 'slow_diabetic_nod_notx_0h_tag_count', 0.289154, suffix='_norm_2')
    
    refseq = grapher.get_refseq(data)
    
    xcolname = 'balb_notx_0h_tag_count'
    ycolname = 'nod_notx_0h_tag_count_norm'
    
    # Remove low tag counts
    refseq = refseq[(refseq[xcolname] > 20) | (refseq[ycolname] > 20)]
    refseq = refseq[refseq['transcript_score'] > 15]
    
    # Remove the strangely large last entry
    #refseq = refseq[refseq[xcolname] < max(refseq[xcolname])]
    
    
    refseq_up_nond = refseq[refseq['balb_nod_notx_0h_fc'] >= 1]
    refseq_down_nond = refseq[refseq['balb_nod_notx_0h_fc'] <= -1]
    
    refseq_up_d = refseq[refseq['diabetic_balb_nod_notx_0h_fc'] >= 1]
    refseq_down_d = refseq[refseq['diabetic_balb_nod_notx_0h_fc'] <= -1]
    
    refseq_up_slowd = refseq[refseq['slow_diabetic_balb_nod_notx_0h_fc'] >= 1]
    refseq_down_slowd = refseq[refseq['slow_diabetic_balb_nod_notx_0h_fc'] <= -1]
    
    if True:
        print set(grapher.get_gene_list(refseq_up_nond)) & set(grapher.get_gene_list(refseq_up_d))
        print set(grapher.get_gene_list(refseq_down_nond)) & set(grapher.get_gene_list(refseq_down_d))
    
    
    if False:
        # non-d
        ax = grapher.scatterplot(refseq, 'balb_notx_0h_tag_count', 'nod_notx_0h_tag_count_norm',
                            log=True, color='blue', master_dataset=refseq,
                            title='BALBc vs. NOD BMDC Refseq Transcripts',
                            show_2x_range=True, show_legend=False,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'nondiabetic_balbc_v_nod_scatterplot.png'))
        grapher.show_plot()
    
    if False:
        # diabetic
        ax = grapher.scatterplot(refseq, 'diabetic_balb_notx_0h_tag_count', 'diabetic_nod_notx_0h_tag_count_norm',
                            log=True, color='blue', master_dataset=refseq,
                            title='Diabetic BALBc vs. NOD BMDC Refseq Transcripts',
                            show_2x_range=True, show_legend=False,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'diabetic_balbc_v_nod_scatterplot.png'))
        grapher.show_plot()
    
    if False:
        # slow-d
        ax = grapher.scatterplot(refseq, 'slow_diabetic_balb_notx_0h_tag_count', 'slow_diabetic_nod_notx_0h_tag_count_norm',
                            log=True, color='blue', master_dataset=refseq,
                            title='Slow-Diabetic BALBc vs. NOD BMDC Refseq Transcripts',
                            show_2x_range=True, show_legend=False,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'slow_diabetic_balbc_v_nod_scatterplot.png'))
        grapher.show_plot()
    
    
    if False:
        gene = 'H2-M2'
        gene_row = refseq[refseq['gene_names'] == ('{%s}' % gene)]
        grapher.bargraph_for_transcript(gene_row, 
                                        ['balb_nod_notx_0h_fc', 'diabetic_balb_nod_notx_0h_fc',
                                         #'slow_diabetic_balb_nod_notx_0h_fc', 
                                         ],
                                        bar_names=['Non-diabetic\nnotx 0h', 
                                                   'Diabetic\nnotx 0h', 
                                                   #'Slow-diabetic\nnotx 0h',
                                                   ],
                                        title='%s Fold Change in NOD vs. BALBc GRO-seq' % gene,
                                        ylabel='Fold Change in NOD vs. BALBc',
                                        show_plot=False)
        grapher.save_plot(os.path.join(dirpath, '%s_fold_change_bargraph.png' % gene.lower()))
        grapher.show_plot()