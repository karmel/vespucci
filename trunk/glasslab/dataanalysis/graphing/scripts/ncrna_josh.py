'''
Created on May 10, 2012

@author: karmel
'''
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher
import os
from matplotlib import pyplot

if __name__ == '__main__':
    grapher = SeqGrapher()
    
    dirpath = '/Users/karmel/Desktop/Projects/GlassLab/Notes_and_Reports/ncRNA_josh/'
    filename = os.path.join(dirpath, 'refseq_predictions.tsv')
    evidence_f = os.path.join(dirpath, 'refseq_evidence.orf')
    data = grapher.import_file(filename)
    evidence = grapher.import_file(evidence_f)
    
    data['score_orf'] = evidence['score']
    data = data[data['score_orf'] < 200]
    
    data_coding = data[data['score'] >= 0]
    data_noncoding = data[data['score'] < 0]
    ax = grapher.scatterplot(data_coding, 'score_orf', 'score', 
                        log=False, color='blue',
                        label='Predicted Coding', add_noise=False, 
                        show_2x_range=False, plot_regression=False, show_count=False, 
                        show_correlation=False, show_legend=False, show_plot=False)
    ax = grapher.scatterplot(data_noncoding, 'score_orf', 'score', 
                        log=False, color='green',
                        title='CPC-derived Coding Potential Predictions for RefSeq mRNA', 
                        xlabel='ORF score', 
                        ylabel='Coding score', 
                        label='Predicted Non-coding', add_noise=False, 
                        show_2x_range=False, plot_regression=False, show_count=False, 
                        show_correlation=False, show_legend=True, show_plot=False, ax=ax)
    pyplot.plot([0,max(data['score_orf'])],[0,0], '-', color='black')
    grapher.save_plot(os.path.join(dirpath, 'refseq_coding_potential_predictions_zoom.png'))
    grapher.show_plot()
    
