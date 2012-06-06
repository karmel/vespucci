'''
Created on Mar 23, 2012

@author: karmel
'''
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import os

if __name__ == '__main__':
    grapher = SeqGrapher()
    
    dirpath = '/Users/karmel/Desktop/Projects/GlassLab/Notes_and_Reports/NOD_BALBc/ThioMacs/Diabetic/Nonplated/Analysis/'
    filename = os.path.join(dirpath, 'balbc_nod_vectors.txt')
    data = grapher.import_file(filename)
    
    data = grapher.normalize(data, 'nod_notx_1h_tag_count', 1.095517)
    data = grapher.normalize(data, 'nod_kla_1h_tag_count', 0.653140)
    data = grapher.normalize(data, 'nonplated_diabetic_nod_notx_tag_count', 0.884956)
    data = grapher.normalize(data, 'nonplated_diabetic_balb_notx_tag_count', 0.645397)
    #data = grapher.normalize(data, 'nonplated_diabetic_nod_notx_tag_count', 2.320349, suffix='_norm2')
    #data = grapher.normalize(data, 'balb_notx_1h_tag_count', 0.486305)
    
    refseq = grapher.get_refseq(data)
    
    xcolname = 'nonplated_diabetic_balb_notx_tag_count'
    ycolname = 'nonplated_diabetic_nod_notx_tag_count_norm'
    
    # Remove low tag counts
    refseq = refseq[(refseq[xcolname] > 20) | (refseq[ycolname] > 20)]
    refseq = refseq[refseq['transcript_score'] > 15]
    
    # Remove the strangely large last entry
    refseq = refseq[refseq[xcolname] < max(refseq[xcolname])]
    
    # Filter out those that are diff because of plating for BALBc, since there appears to be
    # some contamination there
    refseq = refseq[abs(refseq['balb_plating_notx_fc'] <= 1)]
    
    # Split into those that are also diff in non-diabetic NOD and those not
    refseq_diabetic = refseq[abs(refseq['balb_nod_notx_1h_fc']) < 1]
    refseq_strain = refseq[abs(refseq['balb_nod_notx_1h_fc']) >= 1]
    
    refseq_plated_diabetic = refseq_diabetic[abs(refseq_diabetic['diabetic_balb_nod_notx_1h_fc']) >= 1]
    refseq_nonplated_leftover = refseq_diabetic[abs(refseq_diabetic['diabetic_balb_nod_notx_1h_fc']) < 1]
    
    refseq_nonplated_up = refseq[refseq['nonplated_diabetic_balb_nod_notx_fc'] >= 1]
    #refseq_nonplated_up = refseq_nonplated_up[refseq_nonplated_up['balb_nod_notx_1h_fc'] < 1]
    refseq_nonplated_down = refseq[refseq['nonplated_diabetic_balb_nod_notx_fc'] <= -1]
    #refseq_nonplated_down = refseq_nonplated_down[refseq_nonplated_down['balb_nod_notx_1h_fc'] > -1]
    
    refseq_up_nond = refseq[refseq['balb_nod_notx_1h_fc'] >= 1]
    refseq_down_nond = refseq[refseq['balb_nod_notx_1h_fc'] <= -1]
    
    refseq_up_d = refseq[refseq['diabetic_balb_nod_notx_1h_fc'] >= 1]
    refseq_down_d = refseq[refseq['diabetic_balb_nod_notx_1h_fc'] <= -1]
    
    if False:
        print grapher.get_gene_names(refseq_up_nond)
        print grapher.get_gene_names(refseq_down_nond)
        
    if False:
        
        print set(grapher.get_gene_list(refseq_up_nond)) & set(grapher.get_gene_list(refseq_up_d))
        print set(grapher.get_gene_list(refseq_down_nond)) & set(grapher.get_gene_list(refseq_down_d))
    
    if False:
        ax = grapher.scatterplot(refseq_nonplated_leftover, xcolname, ycolname,
                            log=True, color='blue', master_dataset=refseq,
                            xlabel='BALBc notx', ylabel='NOD notx', label='Different only with diabetes when not plated',
                            show_2x_range=False, show_legend=False, 
                            show_count=False, show_correlation=False,
                            show_plot=False)
        ax = grapher.scatterplot(refseq_plated_diabetic, xcolname, ycolname,
                            log=True, color='green', master_dataset=refseq,
                            label='Different in NOD with diabetes (plated),\nbut not without',
                            show_2x_range=False, show_legend=False,
                            show_count=False, show_correlation=False, show_plot=False, ax=ax)
        ax = grapher.scatterplot(refseq_strain, xcolname, ycolname,
                            log=True, color='red', master_dataset=refseq,
                            title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                            label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True,show_plot=False, ax=ax)
        grapher.save_plot(os.path.join(dirpath, 'nonplated_diabetic_nod_vs_balbc_three_groups_scatterplot_filtered.png'))
        grapher.show_plot()
    
    if False:
        ax = grapher.scatterplot(refseq_diabetic, xcolname, ycolname,
                            log=True, color='blue', master_dataset=refseq,
                            xlabel='BALBc notx', ylabel='NOD notx', label='Nonplated BALBc vs. NOD',
                            show_2x_range=False, show_legend=False, 
                            show_count=False, show_correlation=False,
                            show_plot=False)
        ax = grapher.scatterplot(refseq_strain, xcolname, ycolname,
                            log=True, color='red', master_dataset=refseq,
                            title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                            label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False, ax=ax)
        grapher.save_plot(os.path.join(dirpath, 'nonplated_diabetic_nod_vs_balbc_scatterplot_filtered.png'))
        grapher.show_plot()
    
    if False:
        ax = grapher.scatterplot(refseq_diabetic[abs(refseq_diabetic['nonplated_diabetic_balb_nod_notx_fc']) >= 1], 
                                 xcolname, ycolname,
                            log=True, color='blue', master_dataset=refseq[abs(refseq['nonplated_diabetic_balb_nod_notx_fc']) >= 1],
                            xlabel='BALBc notx', ylabel='NOD notx', label='Nonplated BALBc vs. NOD',
                            show_2x_range=False, show_legend=False, 
                            show_count=False, show_correlation=False,
                            show_plot=False)
        ax = grapher.scatterplot(refseq_strain[abs(refseq_strain['nonplated_diabetic_balb_nod_notx_fc']) >= 1], 
                                 xcolname, ycolname,
                            log=True, color='red', master_dataset=refseq[abs(refseq['nonplated_diabetic_balb_nod_notx_fc']) >= 1],
                            title='Differential Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                            label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False, ax=ax)
        grapher.save_plot(os.path.join(dirpath, 'nonplated_diabetic_nod_vs_balbc_scatterplot_up_down.png'))
        grapher.show_plot()
        
        print len(refseq_nonplated_up)
        print len(refseq_nonplated_down)
        print len(refseq_nonplated_up[abs(refseq_nonplated_up['balb_nod_notx_1h_fc']) >= 1])
        print len(refseq_nonplated_down[abs(refseq_nonplated_down['balb_nod_notx_1h_fc']) >= 1])
    if False:
        # Plated Balb vs. non-plated balb
        ax = grapher.scatterplot(refseq, 'diabetic_balb_notx_1h_tag_count', 'nonplated_diabetic_balb_notx_tag_count_norm',
                            log=True, color='blue', master_dataset=refseq,
                            title='Plated BALBc vs. Nonplated BALBc Refseq Transcripts',
                            #label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'plated_balbc_vs_nonplated_balbc_scatterplot.png'))
        grapher.show_plot()
    if False:
        # Plated nod vs. non-plated nod
        ax = grapher.scatterplot(refseq, 'diabetic_nod_notx_1h_tag_count', 'nonplated_diabetic_nod_notx_tag_count_norm2',
                            log=True, color='blue', master_dataset=refseq,
                            title='Plated Diabetic NOD vs. Nonplated Diabetic NOD Refseq Transcripts',
                            #label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'plated_nod_vs_nonplated_nod_scatterplot.png'))
        grapher.show_plot()
    if False:
        # Plated diabetic Balb vs. non-diabetic balb
        ax = grapher.scatterplot(refseq, 'diabetic_balb_notx_1h_tag_count', 'balb_notx_1h_tag_count_norm',
                            log=True, color='blue', master_dataset=refseq,
                            title='Plated Diabetic BALBc vs. Plated Non-Diabetic BALBc Refseq Transcripts',
                            #label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'plated_diabetic_balbc_vs_plated_nondiabetic_balbc_scatterplot.png'))
        grapher.show_plot()
    if True:
        # non-diabetic Balb vs. non-diabetic nod
        ax = grapher.scatterplot(refseq, 'balb_notx_1h_tag_count', 'nod_notx_1h_tag_count_norm',
                            log=True, color='blue', master_dataset=refseq,
                            title='Non-Diabetic BALBc notx 1h vs. Non-Diabetic NOD notx 1h Refseq Transcripts',
                            #label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'nondiabetic_balbc_notx_vs_nondiabetic_nod_notx_scatterplot.png'))
        grapher.show_plot()
    if True:
        # non-diabetic Balb vs. non-diabetic nod
        ax = grapher.scatterplot(refseq, 'balb_kla_1h_tag_count', 'nod_kla_1h_tag_count_norm',
                            log=True, color='blue', master_dataset=refseq,
                            title='Non-Diabetic BALBc KLA 1h vs. Non-Diabetic NOD KLA 1h Refseq Transcripts',
                            #label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'nondiabetic_balbc_kla_vs_nondiabetic_nod_kla_scatterplot.png'))
        grapher.show_plot()
    
    if False:
        genes = ['Clec4e', 'Tlr2', 'Cxcl1','Cxcl2','Siglec1','Tnf','Il1b','Cxcl10','Tlr4',]
        for gene in genes:
            gene_row = refseq[refseq['gene_names'] == ('{%s}' % gene)]
            grapher.bargraph_for_transcript(gene_row, 
                                            ['balb_nod_notx_1h_fc', 'balb_nod_kla_1h_fc',
                                             'diabetic_balb_nod_notx_1h_fc', 'diabetic_balb_nod_kla_1h_fc',
                                             ],#'nonplated_diabetic_balb_nod_notx_fc',],
                                            bar_names=['Non-diabetic\nnotx 1h', 'Non-diabetic\nKLA 1h',
                                                       'Diabetic\nnotx 1h', 'Diabetic\nKLA 1h',
                                                       ],#'Nonplated diabetic\nnotx 1h',],
                                            title='%s Fold Change in NOD vs. BALBc GRO-seq' % gene,
                                            ylabel='Fold Change in NOD vs. BALBc',
                                            show_plot=False)
            grapher.save_plot(os.path.join(dirpath, '%s_fold_change_bargraph.png' % gene.lower()))
            grapher.show_plot()