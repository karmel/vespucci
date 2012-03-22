'''
Created on Mar 20, 2012

@author: karmel

Miscellaneous methods for graphing tag count plots.
'''
from matplotlib import pyplot
from string import capwords
from matplotlib.ticker import ScalarFormatter
import os
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer

class SeqGrapher(TranscriptAnalyzer):
    def scatterplot(self, data, xcolname, ycolname, log=False, color='blue',
                    master_dataset=None,
                    title='', xlabel=None, ylabel=None,
                    label=None,
                    show_2x_range=True, show_count = True, show_correlation=True, 
                    show_legend=True, show_plot=True):
        
        '''
        Designed to show scatterplots of tags by tags for a given run
        
        Sample using two colors: 
        # Split into those that are also diff in non-diabetic NOD and those not
        refseq_diabetic = refseq[abs(refseq['balb_nod_notx_1h_fc']) < 1]
        refseq_strain = refseq[abs(refseq['balb_nod_notx_1h_fc']) >= 1]
        
        ax = grapher.scatterplot(refseq_diabetic, xcolname, ycolname,
                            log=True, color='blue', master_dataset=refseq,
                            title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                            xlabel='BALBc notx', ylabel='NOD notx', label='Different only with diabetes when not plated',
                            show_2x_range=False, show_legend=False, 
                            show_count=False, show_correlation=False, show_plot=False)
        ax = grapher.scatterplot(refseq_strain, xcolname, ycolname,
                            log=True, color='red', master_dataset=refseq,
                            label='Different in NOD without diabetes (plated)',
                            show_2x_range=True, show_legend=True,
                            show_count=True, show_correlation=True, show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'nonplated_diabetic_nod_vs_balbc_scatterplot.png'))
        grapher.show_plot()
        '''
        # Sometimes we want to use a superset of the data for plot setup.
        master_dataset = master_dataset or data
        
        # Set up plot
        ax = pyplot.subplot(111)
        
        # Plot points
        pyplot.plot(data[xcolname], data[ycolname],
                    'o', markerfacecolor='None',
                    markeredgecolor=color, label=label)

        # Log scaled?
        if log:
            if log <= 1: log = 2
            pyplot.xscale('log', basex=log, nonposx='clip')
            pyplot.yscale('log', basey=log, nonposy='clip')
            ax.xaxis.set_major_formatter(ScalarFormatter())
            ax.yaxis.set_major_formatter(ScalarFormatter())
        
        # Labels
        if xlabel is None: xlabel = capwords(xcolname.replace('_',' '))
        if ylabel is None: ylabel = capwords(ycolname.replace('_',' '))
                
        self.add_axis_labels(xlabel, ylabel)
        
        self.add_title(title, ax)
        
        # Show lines at two-fold change?
        if show_2x_range:
            pyplot.plot([1, .5*max(master_dataset[ycolname])], [2, max(master_dataset[ycolname])], '--', color='black', label='Two-fold change')
            pyplot.plot([1, max(master_dataset[xcolname])], [.5, .5*max(master_dataset[xcolname])], '--', color='black')
        
        # Show Pearson correlation and count?
        if show_count: self.show_count_scatterplot(master_dataset, ax)
        if show_correlation: self.show_correlation_scatterplot(master_dataset, xcolname, ycolname, ax)
        
        if show_legend:
            pyplot.legend(loc='upper left')
            
        # Any other operations to tack on?
        self.other_plot()
        
        if show_plot: self.show_plot()
    
        return ax
    
    def show_count_scatterplot(self, data, ax):
        pyplot.text(.75, .125, 'Total count: %d' % len(data),
                        transform=ax.transAxes)
        
    def show_correlation_scatterplot(self, data, xcolname, ycolname, ax):
        pyplot.text(.75, .1, 'r = %.4f' % data[xcolname].corr(data[ycolname]),
                    transform=ax.transAxes)
            
    def show_plot(self): pyplot.show()
    def save_plot(self, filename): pyplot.savefig(filename)
    
    def add_title(self, title, ax):
        pyplot.title(title)
        ax.title.set_y(1.02)   
        
    def add_axis_labels(self, xlabel, ylabel):
        pyplot.xlabel(xlabel, labelpad=10)
        pyplot.ylabel(ylabel, labelpad=10)
        
    def other_plot(self):
        return True
    
    
    def bargraph_for_transcript(self, transcript_row, cols,
                                bar_names=None, 
                                title='', xlabel='', ylabel='',
                                convert_log_to_fc=True, show_2x_range=True,
                                show_plot=True):
        '''
        Designed to draw bar graphs for fold changes across many
        runs for a single transcript.
        
        Sample for creation of bar graph:
        gene_row = refseq[refseq['gene_names'] == '{Clec4e}']
        grapher.bargraph_for_transcript(gene_row, 
                                        ['balb_nod_notx_1h_fc', 'balb_nod_kla_1h_fc',
                                         'diabetic_balb_nod_notx_1h_fc', 'diabetic_balb_nod_kla_1h_fc',
                                         'nonplated_diabetic_balb_nod_notx_fc',],
                                        bar_names=['Non-diabetic\nnotx 1h', 'Non-diabetic\nKLA 1h',
                                                   'Diabetic\nnotx 1h', 'Diabetic\nKLA 1h',
                                                   'Nonplated diabetic\nnotx 1h',],
                                        title='Mincle (Clec4e) Fold Change in NOD vs. BALBc GRO-seq',
                                        ylabel='Fold Change in NOD vs. BALBc',
                                        show_plot=False)
        grapher.save_plot(os.path.join(dirpath, 'clec4e_fold_change_bargraph.png'))
        grapher.show_plot()
        '''
        
        axis_spacer = .2
        bar_width = .8
        xvals = [x + axis_spacer for x in xrange(0,len(cols))]
        
        default_ylabel = 'Fold Change'
        if convert_log_to_fc:
            yvals = [2**transcript_row[col] for col in cols]
        else:
            yvals = [transcript_row[col] for col in cols]
            default_ylabel = 'Log(2) ' + default_ylabel
        
        # Set up plot
        ax = pyplot.subplot(111)
        ax.set_xlim([0,len(cols) + axis_spacer])
        # Show line at zero
        pyplot.plot([0,len(cols) + axis_spacer], [0,0], '-',color='black')
        
        # And at two-fold change
        if show_2x_range and max(yvals) >= 2:
            pyplot.plot([0,len(cols) + axis_spacer], 
                        [convert_log_to_fc and 2 or 1, convert_log_to_fc and 2 or 1, ], 
                        '--',color='black')
            
        ax.bar(xvals, yvals, bar_width, color='#C9D9FB')
        
        ax.set_xticks([x + .5*bar_width for x in xvals])
        ax.set_xticklabels(bar_names or cols)
        
        ylabel = ylabel or default_ylabel
        self.add_axis_labels(xlabel or 'Experimental Conditions', ylabel)
        self.add_title(title, ax)
        
        # Any other operations to tack on?
        self.other_plot()
        
        if show_plot: self.show_plot()
    
        return ax
                
if __name__ == '__main__':
    grapher = SeqGrapher()
    
    dirpath = '/Users/karmel/GlassLab/Notes and Reports/NOD_BALBc/ThioMacs/Diabetic/Nonplated/Analysis/'
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
    