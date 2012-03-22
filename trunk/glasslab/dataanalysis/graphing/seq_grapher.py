'''
Created on Mar 20, 2012

@author: karmel

Miscellaneous methods for graphing tag count plots.
'''
from pandas.io import parsers
from matplotlib import pyplot
from string import capwords
from matplotlib.ticker import ScalarFormatter
import os

class SeqGrapher(object):
    
    def import_file(self, filename, separator='\t', header=True):
        if header: header_row = 0
        else: header_row = None
        data = parsers.read_csv(filename, sep=separator, header=header_row)
        
        return data
    
    def get_refseq(self, data, colname='has_refseq'):
        return data[data[colname] != 0]
    
    def normalize(self, data, colname, normfactor):
        data[colname + '_norm'] = data[colname]*normfactor
        return data
    
    def scatterplot(self, data, xcolname, ycolname, log=False, color='blue',
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
                            log=True, color='blue',
                            title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                            xlabel='BALBc notx', ylabel='NOD notx', label='Different only diabetes',
                            show_2x_range=False, show_legend=False, 
                            show_count=False, show_correlation=False, show_plot=False)
        ax = grapher.scatterplot(refseq_strain, xcolname, ycolname,
                            log=True, color='red',
                            title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                            xlabel='BALBc notx', ylabel='NOD notx', label='Different regardless of diabetes',
                            show_count=False, show_correlation=False, show_plot=False)
        grapher.show_count_scatterplot(refseq, ax)
        grapher.show_correlation_scatterplot(refseq, xcolname, ycolname, ax)
        #grapher.show_plot()
        grapher.save_plot(os.path.join(dirpath, 'nonplated_diabetic_nod_vs_balbc_scatterplot.png'))
        '''
        # Set up plot
        ax = pyplot.subplot(111)
        pyplot.axis([min(data[xcolname]), max(data[xcolname]), min(data[ycolname]), max(data[ycolname])])
        
        # Plot points
        pyplot.plot(data[xcolname], data[ycolname],
                    'o', markerfacecolor='None',
                    markeredgecolor=color, label=label)

        # Log scaled?
        if log:
            if log <= 1: log = 10
            pyplot.xscale('log', basex=log, nonposx='clip')
            pyplot.yscale('log', basey=log, nonposy='clip')
            ax.xaxis.set_major_formatter(ScalarFormatter())
            ax.yaxis.set_major_formatter(ScalarFormatter())
        
        # Labels
        if xlabel is None: xlabel = capwords(xcolname.replace('_',' '))
        if ylabel is None: ylabel = capwords(ycolname.replace('_',' '))
                
        pyplot.xlabel(xlabel, labelpad=10)
        pyplot.ylabel(ylabel)
        
        pyplot.title(title)
        ax.title.set_y(1.02)
        
        # Show lines at two-fold change?
        if show_2x_range:
            pyplot.plot([0, max(data[xcolname])], [0, 2*max(data[xcolname])], '--', color='black', label='Two-fold change')
            pyplot.plot([0, max(data[xcolname])], [0, .5*max(data[xcolname])], '--', color='black')
        
        # Show Pearson correlation and count?
        if show_count: self.show_count_scatterplot(data, ax)
        if show_correlation: self.show_correlation_scatterplot(data, xcolname, ycolname, ax)
        
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
        
    
    def other_plot(self):
        return True
    
    
    def bargraph_for_transcript(self, transcript_row, cols,
                                convert_log_to_fc=True, show_plot=True):
        '''
        Designed to draw bar graphs for fold changes across many
        runs for a single transcript.
        '''
        
        axis_spacer = .2
        xvals = [x + axis_spacer for x in xrange(0,len(cols))]
        if convert_log_to_fc:
            # Show 2**log_val for positive vals; -2**log_val for negative vals.
            yvals = [cmp(transcript_row[col],0)*2**abs(transcript_row[col]) for col in cols]
        else:
            yvals = [transcript_row[col] for col in cols]
        
        # Set up plot
        ax = pyplot.subplot(111)
        ax.set_xlim([0,len(cols) + axis_spacer])
        # Show line at zero
        pyplot.plot([0,len(cols) + axis_spacer], [0,0], '-',color='black')
        
        ax.bar(xvals, yvals, .8, color='#C9D9FB')
        
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
    '''
    ax = grapher.scatterplot(refseq_diabetic, xcolname, ycolname,
                        log=True, color='blue',
                        title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                        xlabel='BALBc notx', ylabel='NOD notx', label='Different only with diabetes',
                        show_2x_range=False, show_legend=False, 
                        show_count=False, show_correlation=False, show_plot=False)
    ax = grapher.scatterplot(refseq_strain, xcolname, ycolname,
                        log=True, color='red',
                        title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                        xlabel='BALBc notx', ylabel='NOD notx', label='Different in NOD without diabetes',
                        show_count=False, show_correlation=False, show_plot=False)
    grapher.show_count_scatterplot(refseq, ax)
    grapher.show_correlation_scatterplot(refseq, xcolname, ycolname, ax)
    grapher.save_plot(os.path.join(dirpath, 'nonplated_diabetic_nod_vs_balbc_scatterplot.png'))
    grapher.show_plot()
    
    '''
    mincle_row = refseq[refseq['gene_names'] == '{Clec4e}']
    grapher.bargraph_for_transcript(mincle_row, 
                                    ['balb_nod_notx_1h_fc', 'balb_nod_kla_1h_fc',
                                     'diabetic_balb_nod_notx_1h_fc', 'diabetic_balb_nod_kla_1h_fc',
                                     'nonplated_diabetic_balb_nod_notx_fc',])
    