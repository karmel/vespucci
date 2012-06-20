'''
Created on Mar 23, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import os

if __name__ == '__main__':
    grapher = SeqGrapher()
    
    dirpath = 'karmel/Desktop/Projects/GlassLab/Notes_and_Reports/NOD_BALBc/ThioMacs/Analysis_2012_06/'
    dirpath = grapher.get_path(dirpath)
    filename = os.path.join(dirpath, 'balbc_nod_vectors.txt')
    data = grapher.import_file(filename)
    
    data = grapher.normalize(data, 'nod_notx_1h_tag_count', 1.095387)
    data = grapher.normalize(data, 'nod_kla_1h_tag_count', 0.653289)
    data = grapher.normalize(data, 'nonplated_diabetic_nod_notx_tag_count', 0.884956)
    data = grapher.normalize(data, 'nonplated_diabetic_balb_notx_tag_count', 0.645397)
    
    data['balb_notx_1h_reads_per_base'] = data['balb_notx_1h_tag_count']/data['length']
    data['balb_kla_1h_reads_per_base'] = data['balb_kla_1h_tag_count']/data['length']
    
    refseq = grapher.get_refseq(data)
    
    # Remove low tag counts
    xcolname = 'balb_kla_1h_tag_count'
    ycolname = 'nod_kla_1h_tag_count_norm'
    refseq = refseq[refseq['transcript_score'] >= 10]
    
    refseq_bg = refseq
    #refseq = refseq[(refseq[xcolname] > 20) | (refseq[ycolname] > 20)]
    
    '''
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
    '''
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
    refseq_up_nond_kla = refseq[refseq['balb_nod_kla_1h_fc'] >= 1]
    refseq_down_nond = refseq[refseq['balb_nod_notx_1h_fc'] <= -1]
    refseq_down_nond_kla = refseq[refseq['balb_nod_kla_1h_fc'] <= -1]
    
    refseq_up_d = refseq[refseq['diabetic_balb_nod_notx_1h_fc'] >= 1]
    refseq_down_d = refseq[refseq['diabetic_balb_nod_notx_1h_fc'] <= -1]
    
    more_up = refseq[(refseq['balb_kla_1h_fc'] >= 1) 
                          & (refseq['balb_kla_1h_fc'] - refseq['nod_kla_1h_fc'] <= -1)]
    less_up = refseq[(refseq['balb_kla_1h_fc'] >= 1) 
                          & (refseq['balb_kla_1h_fc'] - refseq['nod_kla_1h_fc'] >= 1)]
    more_down = refseq[(refseq['balb_kla_1h_fc'] <= -1) 
                          & (refseq['balb_kla_1h_fc'] - refseq['nod_kla_1h_fc'] >= 1)]    
    less_down = refseq[(refseq['balb_kla_1h_fc'] <= -1) 
                          & (refseq['balb_kla_1h_fc'] - refseq['nod_kla_1h_fc'] <= -1)]
    
    if False:
        #print grapher.get_gene_names(refseq_bg)
        print grapher.get_gene_names(refseq_up_nond_kla)
        print grapher.get_gene_names(refseq_down_nond_kla)
        print grapher.get_gene_names(more_up)
        print grapher.get_gene_names(less_up)
        print grapher.get_gene_names(more_down)
        print grapher.get_gene_names(less_down)
        
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
    if False:
        # non-diabetic Balb vs. non-diabetic nod
        ax = grapher.scatterplot(refseq, 'balb_notx_1h_tag_count', 'nod_notx_1h_tag_count_norm',
                            log=True, color='blue', master_dataset=refseq,
                            title='Non-Diabetic BALBc notx 1h vs. Non-Diabetic NOD notx 1h Refseq Transcripts',
                            #label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'nondiabetic_balbc_notx_vs_nondiabetic_nod_notx_scatterplot.png'))
        grapher.show_plot()
    if False:
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
        genes = ['Clec4e', 
                 'Tlr2','Cxcl1','Cxcl2','Cxcl14','Il6','Ptgs2','Tnfsf9','Vegfa','Tnf',
                 'Siglec1','Mmp9','Angpt4',
                 'Il1b','Cxcl10','Tlr4','Il12b']
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
    if True:
        genes = ['Tlr2','Cxcl1','Cxcl2','Il6','Ptgs2','Tnfsf9','Vegfa','Tnf',
                 'Siglec1','Mmp9',
                 'Il10','Il1b','Cxcl10','Tlr4','Il12b']
        
        genes = list(set(genes) & set(grapher.get_gene_list(refseq)))
        indices = [refseq[refseq['gene_names'] == ('{%s}' % gene)].index[0] for gene in genes]
        
        
        sorted_by_count = refseq.fillna(0).sort_index(axis=0, by='balb_notx_1h_reads_per_base').index.copy()
        sort_indexes = list(enumerate(sorted_by_count))
        sort_indexes.sort(key=lambda x: x[1])
        refseq['rank'] = zip(*sort_indexes)[0]
         
        grapher.bargraph_for_transcripts(refseq, indices, ['balb_nod_notx_1h_fc'],
                                            bar_names=genes,
                                            title='Fold Change in NOD vs. BALBc notx 1h GRO-seq',
                                            ylabel='Fold Change in NOD vs. BALBc',
                                            rank_label='Rank of read per base pair value in BALBc notx 1h, ascending',
                                            show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'notx_1h_phagocytosis_fold_change_bargraph.png'))
        grapher.show_plot()
            
    if True:
        genes = ['Tlr2','Cxcl1','Cxcl2','Il6','Ptgs2','Tnfsf9','Vegfa','Tnf',
                 'Siglec1','Mmp9',
                 'Il10','Il1b','Cxcl10','Tlr4','Il12b']
        #genes = ['Myo5a', 'Myh10', 'Myh9', 'Myl12a', 'Myl12b', 'Myl9', 'Shroom1', 'Shroom4', 'Myh1', 'Myh1', 'Myh11', 'Myh11', 'Myh2', 'Myh6', 'Myh7', 'Ttn', 'Bmf', 'Bmf', 'Cgnl1', 'Dynll2', 'Myh1', 'Myh1', 'Myh10', 'Myh10', 'Myh10', 'Myh11', 'Myh13', 'Myh14', 'Myh15', 'Myh2', 'Myh3', 'Myh4', 'Myh4', 'Myh6', 'Myh6', 'Myh6', 'Myh7', 'Myh7', 'Myh7b', 'Myh7b', 'Myh8', 'Myh9', 'Myh9', 'Myh9', 'Myl1', 'Myl12b', 'Myl2', 'Myl3', 'Myl6', 'Myl6b', 'Myl7', 'Myl9', 'Mylpf', 'Myo10', 'Myo10', 'Myo15', 'Myo15', 'Myo16', 'Myo16', 'Myo18a', 'Myo18a', 'Myo18b', 'Myo19', 'Myo19', 'Myo1a', 'Myo1a', 'Myo1b', 'Myo1b', 'Myo1c', 'Myo1d', 'Myo1d', 'Myo1e', 'Myo1e', 'Myo1f', 'Myo1g', 'Myo1g', 'Myo1h', 'Myo1h', 'Myo3a', 'Myo3b', 'Myo3b', 'Myo5a', 'Myo5a', 'Myo5b', 'Myo5c', 'Myo6', 'Myo7a', 'Myo7b', 'Myo7b', 'Myo9a', 'Myo9a', 'Myo9b', 'Mybpc2', 'Mybph', 'Myh1', 'Myh13', 'Myh15', 'Myh2', 'Myh3', 'Myh4', 'Myh6', 'Myh7', 'Myh7b', 'Myh8', 'Myom1', 'Myo7a', 'Myo1c', 'Myl6', 'Myl6b', 'Myo18b', 'Mybpc3', 'Mybpc3', 'Obscn', 'Trim32']
        #genes = ['Abca1', 'Aif1', 'Clec7a', 'Elmo1', 'Elmo1', 'Fcer1g', 'Fcer1g', 'Fcer1g', 'Fcgr1', 'Fcgr1', 'Fcgr1', 'Fcgr2b', 'Fcgr3', 'Fcgr3', 'Fcgr3', 'Gulp1', 'Havcr1', 'Igh-8', 'Igh-8', 'Igh-8', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2b', 'Ighg2b', 'Ighg2b', 'Ighg2b', 'Mfge8', 'Rac1', 'Sirpa', 'Vamp7', 'Vamp7', 'Itgav', 'Cd209b', 'Cd36', 'Clec7a', 'Clec7a', 'Colec12', 'Colec12', 'Fcgr1', 'Fcgr1', 'Fcgr1', 'Fcgr3', 'Fcgr3', 'Fcgr3', 'Igh-8', 'Igh-8', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2b', 'Ighg2b', 'Ighg2b', 'Mfge8', 'Scarb1', 'Sirpa', 'Cd36', 'Cd36', 'F2rl1', 'Itga2', 'Nckap1l', 'Rac1', 'Thbs1', 'Axl', 'Axl', 'Axl', 'Ccr2', 'Cd36', 'Gas6', 'Gas6', 'Itgav', 'Jmjd6', 'Jmjd6', 'Jmjd6', 'Lrp1', 'Mertk', 'Mertk', 'Mertk', 'Nr1h3', 'Rara', 'Tgm2', 'Tyro3', 'Tyro3', 'Hmgb1', 'Abr', 'Ahsg', 'Bcr', 'C3', 'Calr', 'Camk1d', 'Ccr7', 'Cd209b', 'Cd47', 'Clec7a', 'Fcer1g', 'Fcer1g', 'Fcer1g', 'Fcgr1', 'Fcgr1', 'Fcgr1', 'Fcgr2b', 'Fcgr3', 'Fcgr3', 'Fcgr3', 'Gas6', 'Gata2', 'Igh-8', 'Igh-8', 'Igh-8', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg1', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2a', 'Ighg2b', 'Ighg2b', 'Ighg2b', 'Ighg2b', 'Mbl1', 'Mbl2', 'Mertk', 'Mfge8', 'Nod2', 'Pros1', 'Ptk2', 'Ptx3', 'Sftpa1', 'Sftpd', 'Sirpa', 'Sirpb1a', 'Slc11a1', 'Slc11a1', 'Tub', 'Tulp1', 'Jmjd6', 'Megf10', 'Megf10', 'Pear1', 'Pear1', 'Scarb1', 'Scarb1', 'Scarb1', 'Coro1a', 'Coro1a', 'Myo7a', 'P2rx7', 'Ccl2', 'Mfge8', 'Fgr', 'Hck', 'Itgav', 'Itgav', 'Scarb1', 'Syk', 'Adipoq', 'Cnn2', 'Csk', 'Fcgr2b', 'Gnb2l1', 'Prtn3', 'Pten', 'Sftpd', 'Tgfb1', 'Cd47', 'Lbp', 'Ptx3', 'Sftpd', 'Abca7', 'Anxa3', 'Axl', 'Axl', 'Cd302', 'Cdc42se1', 'Cdc42se2', 'Cebpe', 'Cebpe', 'Coro1a', 'Coro1c', 'Dock1', 'Elane', 'Elmo1', 'Elmo2', 'Elmo2', 'Elmo3', 'Elmo3', 'Elmod1', 'Elmod2', 'Elmod3', 'Gas6', 'Gata2', 'Gulp1', 'Hck', 'hem1', 'Icam5', 'Irf8', 'Megf10', 'Mertk', 'Mertk', 'Myo7a', 'Pecam1', 'Pip5k1c', 'Slc11a1', 'Tub', 'Tulp1', 'Unc13d', 'Vav1']
        
        genes = list(set(genes) & set(grapher.get_gene_list(refseq)))
        indices = [refseq[refseq['gene_names'] == ('{%s}' % gene)].index[0] for gene in genes]
        
        
        sorted_by_count = refseq.fillna(0).sort_index(axis=0, by='balb_kla_1h_reads_per_base').index.copy()
        sort_indexes = list(enumerate(sorted_by_count))
        sort_indexes.sort(key=lambda x: x[1])
        refseq['rank'] = zip(*sort_indexes)[0]
         
        grapher.bargraph_for_transcripts(refseq, indices, ['balb_nod_kla_1h_fc'],
                                            bar_names=genes,
                                            title='Fold Change in NOD vs. BALBc KLA 1h GRO-seq',
                                            ylabel='Fold Change in NOD vs. BALBc',
                                            rank_label='Rank of read per base pair value in BALBc KLA 1h, ascending',
                                            show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'kla_1h_phagocytosis_fold_change_bargraph.png'))
        grapher.show_plot()
            