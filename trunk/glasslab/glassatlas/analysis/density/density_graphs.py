'''
Created on Feb 18, 2011

@author: karmel

An alternate approach to stitching together transcripts:
Graph according to position and density, and find clusters
within the graph.
'''
from __future__ import division
from glasslab.config import current_settings
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from django.db.models.aggregates import Sum, Count
from matplotlib import pyplot
from django.db import connection

class DensityAnalyzer(object):
    cell_base = CellTypeBase().get_cell_type_base(current_settings.CURRENT_CELL_TYPE)()
    
    def get_transcripts_for_chromosome(self, chr_id, strand=0):
        '''
        Get transcripts by chromosome and strand; annotate with length, tag_count,
        and number of runs present.
        '''
        trans = self.cell_base.glass_transcript.objects.filter(chromosome__id=chr_id, strand=strand)
        trans = trans.extra(select={'length': '(transcription_end - transcription_start)'})
        trans = trans.annotate(tag_count=Sum('glasstranscriptsource__tag_count'))
        trans = trans.annotate(run_count=Count('glasstranscriptsource__sequencing_run'))
        trans = trans.order_by('transcription_start')
        return trans
    
    def graph_density(self):
        '''
        Graph transcripts according to position on chromosome/strand (x-axis),
        and per-run density over that area.
        '''
        # Set up pyplot
        for chr_id in (21,22):
            pyplot.figure(figsize=(24,24))
            for strand in (0,1):
                # Set up subplot
                ax = pyplot.subplot(211 + strand)
                ax.set_yscale('log', basey=2)
                pyplot.title('Transcript region density: Chromosome %d, strand %s' % (chr_id, strand and '-' or '+'))
                pyplot.xlabel('Position on chromosome' )
                pyplot.ylabel('Average density (tags/run/bp)')
                transcripts = self.get_transcripts_for_chromosome(chr_id, strand)
                
                for trans in transcripts:
                    # Add line from start to end pos, with avg density as y val
                    x = [trans.transcription_start, trans.transcription_end]
                    density = trans.tag_count/trans.run_count/trans.length
                    y = [density]*2
                    pyplot.plot(x,y, color='black')

                connection.close()
                
            pyplot.savefig('/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Glass Atlas/density_analysis/pyplot2/density_graph_%d.png' % chr_id)

    def density_csv(self):
        for chr_id in (22,):
            
            for strand in (0,1):
                transcripts = self.get_transcripts_for_chromosome(chr_id, strand)
                output = ''
                for trans in transcripts:
                    # Add line from start to end pos, with avg density as y val
                    x = [str(trans.transcription_start), str(trans.transcription_end)]
                    density = trans.tag_count/trans.run_count/trans.length
                    y = [str(density)]*2
                    output += ','.join(x) + ',' + ','.join(y) + '\n'
                connection.close()
                f = open('/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Glass Atlas/density_analysis/transcript_data/transcript_data_chr_%d_strand_%d.csv' % (chr_id, strand), 'w')
                f.write(output)

if __name__ == '__main__':
    da = DensityAnalyzer()
    da.graph_density()