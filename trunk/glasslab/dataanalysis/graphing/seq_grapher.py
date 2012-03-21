'''
Created on Mar 20, 2012

@author: karmel

Miscellaneous methods for graphing tag count plots.
'''
from pandas.io import parsers
from matplotlib import pyplot
from string import capwords
from matplotlib.ticker import ScalarFormatter

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
                
        pyplot.xlabel(xlabel)
        pyplot.ylabel(ylabel)
        
        pyplot.title(title)
        
        # Show lines at two-fold change?
        if show_2x_range:
            pyplot.plot([0, max(data[xcolname])], [0, 2*max(data[xcolname])], '--', color='black', label='Two-fold change')
            pyplot.plot([0, max(data[xcolname])], [0, .5*max(data[xcolname])], '--', color='black')
        
        # Show Pearson correlation?
        if show_count: self.show_count(data, ax)
        if show_correlation: self.show_correlation(data, xcolname, ycolname, ax)
        
        if show_legend:
            pyplot.legend(loc='upper left')
            
        # Any other operations to tack on?
        self.other_plot()
        
        if show_plot: self.show_plot()
    
        return ax
    
    def show_count(self, data, ax):
        pyplot.text(.75, .125, 'Total count: %d' % len(data),
                        transform=ax.transAxes)
        
    def show_correlation(self, data, xcolname, ycolname, ax):
        pyplot.text(.75, .1, 'r = %.4f' % data[xcolname].corr(data[ycolname]),
                    transform=ax.transAxes)
            
    def show_plot(self): pyplot.show()
        
    
    def other_plot(self):
        return True
    
if __name__ == '__main__':
    grapher = SeqGrapher()
    
    filename = '/Users/karmel/GlassLab/Notes and Reports/NOD_BALBc/ThioMacs/Diabetic/Nonplated/Analysis/balbc_nod_vectors.txt'
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
    
    ax = grapher.scatterplot(refseq_diabetic, xcolname, ycolname,
                        log=True, color='blue',
                        title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                        xlabel='BALBc notx', ylabel='NOD notx', label='Different only diabetes',
                        show_2x_range=False, show_legend=False, 
                        show_count = False, show_correlation=False, show_plot=False)
    ax = grapher.scatterplot(refseq_strain, xcolname, ycolname,
                        log=True, color='red',
                        title='Nonplated Diabetic NOD vs. BALBc Refseq Transcripts',
                        xlabel='BALBc notx', ylabel='NOD notx', label='Different regardless of diabetes',
                        show_count = False, show_correlation=False, show_plot=False)
    grapher.show_count(refseq, ax)
    grapher.show_correlation(refseq, xcolname, ycolname, ax)