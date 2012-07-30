'''
Created on Jul 11, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher

if __name__ == '__main__':
    yzer = SeqGrapher()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/'
    dirpath = yzer.get_path(dirpath)
    img_dirpath = yzer.get_and_create_path(dirpath,'GR Chip', 'peak_tag_count_comparisons')
    
    
    data = yzer.import_file(yzer.get_filename(dirpath, 'transcript_vectors.txt'))
    
    data = data.fillna(0)
    #data = data[(data['distal'] == 't')]
    
    not_trans =data[((data['kla_1_lfc'] >= 1) & (data['dex_over_kla_1_lfc'] > -.58)) 
                    | ((data['kla_2_lfc'] >= 1) & (data['dex_over_kla_2_lfc'] > -.58))
                    | ((data['kla_3_lfc'] >= 1) & (data['dex_over_kla_3_lfc'] > -.58)) 
                    | ((data['kla_4_lfc'] >= 1) & (data['dex_over_kla_4_lfc'] > -.58))
                    ]
    transrepressed = data[((data['kla_1_lfc'] >= 1) & (data['dex_over_kla_1_lfc'] <= -.58)) 
                    | ((data['kla_2_lfc'] >= 1) & (data['dex_over_kla_2_lfc'] <= -.58))
                    | ((data['kla_3_lfc'] >= 1) & (data['dex_over_kla_3_lfc'] <= -.58)) 
                    | ((data['kla_4_lfc'] >= 1) & (data['dex_over_kla_4_lfc'] <= -.58))
                    ]
    
    
    print len(not_trans)
    print len(transrepressed)
    
    xcolname, ycolname = 'p65_kla_tag_count', 'p65_kla_dex_tag_count',
    #xcolname, ycolname = 'gr_dex_tag_count', 'gr_kla_dex_tag_count',
    if True:
        ax = yzer.scatterplot(not_trans, xcolname, ycolname,
                            log=False, color='blue', master_dataset=data,
                            xlabel='p65 KLA tag count', ylabel='p65 KLA+Dex tag count', 
                            label='Up in KLA, not transrepressed',
                            show_2x_range=False, show_legend=False, 
                            show_count=False, show_correlation=False,
                            show_plot=False)
        ax = yzer.scatterplot(transrepressed, xcolname, ycolname,
                            log=False, color='red', master_dataset=data,
                            title='Peak Tag Count Comparison: All transcripts',
                            label='Up in KLA, transrepressed >= 1.5x in KLA+Dex',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False, ax=ax)
        ax.set_xlim([0,800])
        ax.set_ylim([0,800])
        yzer.save_plot(yzer.get_filename(img_dirpath, '{0}_vs_{1}_all.png'.format(xcolname, ycolname)))
        yzer.show_plot()
    