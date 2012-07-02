'''
Created on Jun 26, 2012

@author: karmel
'''
from glasslab.dataanalysis.misc.gr_project_2012.elongation import set_up_sequencing_run_ids, \
    get_sequencing_run_id_sets
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
from glasslab.dataanalysis.motifs.motif_analyzer import MotifAnalyzer


if __name__ == '__main__':
    grapher = SeqGrapher()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/'
    dirpath = grapher.get_path(dirpath)
    filename = grapher.get_filename(dirpath, 'transcript_vectors.txt')
    
    data = grapher.import_file(filename)
    
    run_ids = set_up_sequencing_run_ids()
    dmso, kla, kla_dex, all_dmso, all_kla, all_kla_dex = get_sequencing_run_id_sets()
    
    # Norm sum scalars listed for all, group 1, group 2, group 3, group 4
    kla_scalars = [1.223906, 1.281572, 1.118363, 1.104860, 1.503260]
    kla_dex_scalars = [1.182574, 1.147695, 1.248636, 1.069588, 1.388871]
    dex_over_kla_scalars = [1.069073, 0.967659, 1.122628, 1.008758, 0.927466]
    
    for i, scalar in enumerate(kla_scalars):
        data = grapher.normalize(data, 'kla_{0}tag_count'.format(i and '{0}_'.format(i) or ''), scalar)
    for i, scalar in enumerate(kla_dex_scalars):
        data = grapher.normalize(data, 'kla_dex_{0}tag_count'.format(i and '{0}_'.format(i) or ''), scalar)
    for i, scalar in enumerate(dex_over_kla_scalars):
        data = grapher.normalize(data, 'kla_dex_{0}tag_count'.format(i and '{0}_'.format(i) or ''), 
                                 scalar, suffix='_norm_2')
    
    refseq = data[data['has_refseq'] != 0]    
    refseq = refseq[refseq['transcript_score'] >= 10]
    
    scatter_dirpath = grapher.get_filename(dirpath, 'scatterplots')
    
    #############################################
    # One color tag counts
    #############################################
    if False:
        for dataset, label in ((data, 'all transcripts'),(refseq,'RefSeq')):
            slug_label = label.lower().replace(' ','_')
            # All DMSO vs. all KLA
            ax = grapher.scatterplot(dataset, 'dmso_tag_count', 'kla_tag_count_norm',
                                log=True, color='blue', 
                                title='DMSO vs. KLA tag counts: All runs, {0}'.format(label),
                                xlabel='DMSO 2h tags', ylabel='KLA 1h + DMSO 2h tags', 
                                show_2x_range=True, show_legend=True, 
                                show_count=True, show_correlation=True,
                                show_plot=False)
            grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                'dmso_vs_kla_all_runs_{0}.png'.format(slug_label)))
            grapher.show_plot()
            
            
            for x in xrange(1,5):
                # By group
                ax = grapher.scatterplot(dataset, 
                                    'dmso_{0}_tag_count'.format(x), 'kla_{0}_tag_count_norm'.format(x),
                                    log=True, color='blue', 
                                    title='DMSO vs. KLA tag counts: Group {0} runs, {1}'.format(x, label),
                                    xlabel='DMSO 2h tags', ylabel='KLA 1h + DMSO 2h tags', 
                                    show_2x_range=True, show_legend=True, 
                                    show_count=True, show_correlation=True,
                                    show_plot=False)
                grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                    'dmso_vs_kla_group_{0}_runs_{1}.png'.format(x, slug_label)))
                grapher.show_plot()
    
    if False:
        for dataset, label in ((data, 'all transcripts'),(refseq,'RefSeq')):
            slug_label = label.lower().replace(' ','_')
            # All DMSO vs. all KLA+Dex
            ax = grapher.scatterplot(dataset, 'dmso_tag_count', 'kla_dex_tag_count_norm',
                                log=True, color='blue', 
                                title='DMSO vs. KLA + Dex tag counts: All runs, {0}'.format(label),
                                xlabel='DMSO 2h tags', ylabel='KLA 1h + Dex 2h tags', 
                                show_2x_range=True, show_legend=True, 
                                show_count=True, show_correlation=True,
                                show_plot=False)
            grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                'dmso_vs_kla_dex_all_runs_{0}.png'.format(slug_label)))
            grapher.show_plot()
            
            
            for x in xrange(1,5):
                # By group
                ax = grapher.scatterplot(dataset, 
                                    'dmso_{0}_tag_count'.format(x), 'kla_dex_{0}_tag_count_norm'.format(x),
                                    log=True, color='blue', 
                                    title='DMSO vs. KLA + Dex tag counts: Group {0} runs, {1}'.format(x, label),
                                    xlabel='DMSO 2h tags', ylabel='KLA 1h + Dex 2h tags', 
                                    show_2x_range=True, show_legend=True, 
                                    show_count=True, show_correlation=True,
                                    show_plot=False)
                grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                    'dmso_vs_kla_dex_group_{0}_runs_{1}.png'.format(x, slug_label)))
                grapher.show_plot()
    
    
    if False:
        for dataset, label in ((data, 'all transcripts'),(refseq,'RefSeq')):
            slug_label = label.lower().replace(' ','_')
            # All DMSO vs. all KLA+Dex
            ax = grapher.scatterplot(dataset, 'kla_tag_count', 'kla_dex_tag_count_norm_2',
                                log=True, color='blue', 
                                title='KLA vs. KLA + Dex tag counts: All runs, {0}'.format(label),
                                xlabel='KLA 1h + DMSO 2h tags', ylabel='KLA 1h + Dex 2h tags', 
                                show_2x_range=True, show_legend=True, 
                                show_count=True, show_correlation=True,
                                show_plot=False)
            grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                'kla_vs_kla_dex_all_runs_{0}.png'.format(slug_label)))
            grapher.show_plot()
            
            
            for x in xrange(1,5):
                # By group
                ax = grapher.scatterplot(dataset, 
                                    'kla_{0}_tag_count'.format(x), 'kla_dex_{0}_tag_count_norm_2'.format(x),
                                    log=True, color='blue', 
                                    title='KLA vs. KLA + Dex tag counts: Group {0} runs, {1}'.format(x, label),
                                    xlabel='KLA 1h + DMSO 2h tags', ylabel='KLA 1h + Dex 2h tags', 
                                    show_2x_range=True, show_legend=True, 
                                    show_count=True, show_correlation=True,
                                    show_plot=False)
                grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                    'kla_vs_kla_dex_group_{0}_runs_{1}.png'.format(x, slug_label)))
                grapher.show_plot()

    #############################################
    # Two color tag counts
    #############################################
    if False:
        for dataset, label in ((data, 'all transcripts'),(refseq,'RefSeq')):
            slug_label = label.lower().replace(' ','_')
            # All DMSO vs. all KLA
            up_in_kla = dataset[dataset['kla_lfc'] >= 1]
            else_in_kla = dataset[dataset['kla_lfc'] < 1]
            
            ax = grapher.scatterplot(else_in_kla, 
                                'dmso_tag_count', 'kla_dex_tag_count_norm',
                                master_dataset=dataset,
                                log=True, color='blue', label='Not 2x up in KLA',
                                show_2x_range=False, show_legend=False, 
                                show_count=False, show_correlation=False,
                                show_plot=False)
            ax = grapher.scatterplot(up_in_kla, 
                                'dmso_tag_count', 'kla_dex_tag_count_norm',
                                master_dataset=dataset,
                                log=True, color='red', label='At least 2x up in KLA',
                                title='DMSO vs. KLA + Dex tag counts: All runs, {0}'.format(label),
                                xlabel='DMSO 2h tags', ylabel='KLA 1h + Dex 2h tags', 
                                show_2x_range=True, show_legend=True, 
                                show_count=True, show_correlation=True,
                                show_plot=False, ax=ax)
            grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                'two_color_dmso_vs_kla_dex_all_runs_{0}.png'.format(slug_label)))
            grapher.show_plot()
            
            
            for x in xrange(1,5):
                # By group
                ax = grapher.scatterplot(else_in_kla, 
                                'dmso_{0}_tag_count'.format(x), 'kla_dex_{0}_tag_count_norm'.format(x),
                                master_dataset=dataset,
                                log=True, color='blue', label='Not 2x up in KLA',
                                show_2x_range=False, show_legend=False, 
                                show_count=False, show_correlation=False,
                                show_plot=False)
                ax = grapher.scatterplot(up_in_kla, 
                                'dmso_{0}_tag_count'.format(x), 'kla_dex_{0}_tag_count_norm'.format(x),
                                master_dataset=dataset,
                                log=True, color='red', label='At least 2x up in KLA',
                                title='DMSO vs. KLA + Dex tag counts: Group {0} runs, {1}'.format(x, label),
                                xlabel='DMSO 2h tags', ylabel='KLA 1h + Dex 2h tags', 
                                show_2x_range=True, show_legend=True, 
                                show_count=True, show_correlation=True,
                                show_plot=False, ax=ax)
                grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                    'two_color_dmso_vs_kla_dex_group_{0}_runs_{1}.png'.format(x, slug_label)))
                grapher.show_plot()
    
    if False:
        for dataset, label in ((data, 'all transcripts'),(refseq,'RefSeq')):
            slug_label = label.lower().replace(' ','_')
            # All DMSO vs. all KLA
            up_in_kla = dataset[dataset['kla_lfc'] >= 1]
            else_in_kla = dataset[dataset['kla_lfc'] < 1]
            
            ax = grapher.scatterplot(else_in_kla, 
                                'kla_tag_count', 'kla_dex_tag_count_norm_2',
                                master_dataset=dataset,
                                log=True, color='blue', label='Not 2x up in KLA',
                                show_2x_range=False, show_legend=False, 
                                show_count=False, show_correlation=False,
                                show_plot=False)
            ax = grapher.scatterplot(up_in_kla, 
                                'kla_tag_count', 'kla_dex_tag_count_norm_2',
                                master_dataset=dataset,
                                log=True, color='red', label='At least 2x up in KLA',
                                title='KLA vs. KLA + Dex tag counts: All runs, {0}'.format(label),
                                xlabel='KLA 1h + DMSO 2h tags', ylabel='KLA 1h + Dex 2h tags', 
                                show_2x_range=1.5, show_legend=True, 
                                show_count=True, show_correlation=True,
                                show_plot=False, ax=ax)
            grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                'two_color_kla_vs_kla_dex_all_runs_{0}.png'.format(slug_label)))
            grapher.show_plot()
            
            
            for x in xrange(1,5):
                # By group
                ax = grapher.scatterplot(else_in_kla, 
                                'kla_{0}_tag_count'.format(x), 'kla_dex_{0}_tag_count_norm_2'.format(x),
                                master_dataset=dataset,
                                log=True, color='blue', label='Not 2x up in KLA',
                                show_2x_range=False, show_legend=False, 
                                show_count=False, show_correlation=False,
                                show_plot=False)
                ax = grapher.scatterplot(up_in_kla, 
                                'kla_{0}_tag_count'.format(x), 'kla_dex_{0}_tag_count_norm_2'.format(x),
                                master_dataset=dataset,
                                log=True, color='red', label='At least 2x up in KLA',
                                title='KLA vs. KLA + Dex tag counts: Group {0} runs, {1}'.format(x, label),
                                xlabel='KLA 1h + DMSO 2h tags', ylabel='KLA 1h + Dex 2h tags', 
                                show_2x_range=1.5, show_legend=True, 
                                show_count=True, show_correlation=True,
                                show_plot=False, ax=ax)
                grapher.save_plot(grapher.get_filename(scatter_dirpath, 
                                    'two_color_kla_vs_kla_dex_group_{0}_runs_{1}.png'.format(x, slug_label)))
                grapher.show_plot()


    if False:
        # Gene names
        print grapher.get_gene_names(refseq[(refseq['kla_1_lfc'] >= 1)], add_quotes=True)
        print grapher.get_gene_names(refseq[(refseq['kla_1_lfc'] >= 1) & (refseq['dex_over_kla_1_lfc'] < -.58)])

    if True:
        yzer = MotifAnalyzer()
        motif_dirpath = yzer.get_filename(dirpath,'motifs/size_200')
        distal = data[data['distal'] == 't']
        
        dataset = distal[(distal['kla_lfc'] >= 1)]
        yzer.prep_files_for_homer(dataset, 'distal_up_in_kla_all', motif_dirpath, 
                                  center=False, reverse=False, preceding=True, size=200)
        
        dataset = distal[(distal['kla_1_lfc'] >= 1)]
        yzer.prep_files_for_homer(dataset, 'distal_up_in_kla_1', motif_dirpath, 
                                  center=False, reverse=False, preceding=True, size=200)
        
        
        dataset = distal[(distal['kla_2_lfc'] >= 1)]
        yzer.prep_files_for_homer(dataset, 'distal_up_in_kla_2', motif_dirpath, 
                                  center=False, reverse=False, preceding=True, size=200)
        
        
        dataset = distal[(distal['kla_3_lfc'] >= 1)]
        yzer.prep_files_for_homer(dataset, 'distal_up_in_kla_3', motif_dirpath, 
                                  center=False, reverse=False, preceding=True, size=200)
        
        
        dataset = distal[(distal['kla_4_lfc'] >= 1)]
        yzer.prep_files_for_homer(dataset, 'distal_up_in_kla_4', motif_dirpath, 
                                  center=False, reverse=False, preceding=True, size=200)
        
        


