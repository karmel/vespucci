'''
Created on Mar 23, 2012

@author: karmel
'''
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import os

if __name__ == '__main__':
    grapher = SeqGrapher()
    
    dirpath = '/Users/karmel/GlassLab/Notes_and_Reports/NOD_BALBc/ThioMacs/Diabetic/Nonplated/Analysis/'
    filename = os.path.join(dirpath, 'balbc_nod_vectors.txt')
    data = grapher.import_file(filename)
    
    data = grapher.normalize(data, 'nonplated_diabetic_nod_notx_tag_count', 0.884882)
    
    refseq = grapher.get_refseq(data)
    
    xcolname = 'nonplated_diabetic_balb_notx_tag_count'
    ycolname = 'nonplated_diabetic_nod_notx_tag_count_norm'
    
    # Remove the last entry, which is huge,,,
    refseq = refseq[refseq[xcolname] < max(refseq[xcolname])]
    
    
    # Split into those that are also diff in non-diabetic NOD and those not
    refseq_diabetic = refseq[abs(refseq['balb_nod_notx_1h_fc']) < 1]
    refseq_strain = refseq[abs(refseq['balb_nod_notx_1h_fc']) >= 1]
    
    refseq_plated_diabetic = refseq_diabetic[abs(refseq_diabetic['diabetic_balb_nod_notx_1h_fc']) >= 1]
    refseq_nonplated_leftover = refseq_diabetic[abs(refseq_diabetic['diabetic_balb_nod_notx_1h_fc']) < 1]
    
    refseq_nonplated_up = refseq[refseq['nonplated_diabetic_balb_nod_notx_fc'] >= 1]
    #refseq_nonplated_up = refseq_nonplated_up[refseq_nonplated_up['balb_nod_notx_1h_fc'] < 1]
    refseq_nonplated_down = refseq[refseq['nonplated_diabetic_balb_nod_notx_fc'] <= -1]
    #refseq_nonplated_down = refseq_nonplated_down[refseq_nonplated_down['balb_nod_notx_1h_fc'] > -1]
    
    print grapher.get_gene_names(refseq_nonplated_up)
    print grapher.get_gene_names(refseq_nonplated_down)
    
    ''' 
    ax = grapher.scatterplot(refseq_nonplated_leftover, xcolname, ycolname,
                        log=True, color='blue', master_dataset=refseq,
                        xlabel='BALBc notx', ylabel='NOD notx', label='Different only with diabetes when not plated',
                        show_2x_range=False, show_legend=False, 
                        show_count=False, show_correlation=False, show_plot=False)
    ax = grapher.scatterplot(refseq_plated_diabetic, xcolname, ycolname,
                        log=True, color='green', master_dataset=refseq,
                        label='Different in NOD with diabetes (plated),\nbut not without',
                        show_2x_range=False, show_legend=False, 
                        show_count=False, show_correlation=False, show_plot=False)
    ax = grapher.scatterplot(refseq_strain, xcolname, ycolname,
                        log=True, color='red', master_dataset=refseq,
                        title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                        label='Different in NOD without diabetes (plated)',
                        show_2x_range=True, show_legend=True,
                        show_count=True, show_correlation=True, show_plot=False)
    grapher.save_plot(os.path.join(dirpath, 'nonplated_diabetic_nod_vs_balbc_three_groups_scatterplot.png'))
    grapher.show_plot()
    
    '''
    gene_row = refseq[refseq['gene_names'] == '{Insr}']
    grapher.bargraph_for_transcript(gene_row, 
                                    ['balb_nod_notx_1h_fc', 'balb_nod_kla_1h_fc',
                                     'diabetic_balb_nod_notx_1h_fc', 'diabetic_balb_nod_kla_1h_fc',
                                     'nonplated_diabetic_balb_nod_notx_fc',],
                                    bar_names=['Non-diabetic\nnotx 1h', 'Non-diabetic\nKLA 1h',
                                               'Diabetic\nnotx 1h', 'Diabetic\nKLA 1h',
                                               'Nonplated diabetic\nnotx 1h',],
                                    title='Insr Fold Change in NOD vs. BALBc GRO-seq',
                                    ylabel='Fold Change in NOD vs. BALBc',
                                    show_plot=False)
    grapher.save_plot(os.path.join(dirpath, 'insr_fold_change_bargraph.png'))
    grapher.show_plot()