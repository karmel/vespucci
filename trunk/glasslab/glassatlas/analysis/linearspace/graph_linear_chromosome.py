'''
Created on Apr 5, 2011

@author: karmel

Methods for drawing transcripts along the linear chromosome, separated by sample conditions.
'''
from glasslab.glassatlas.datatypes.transcript import CellTypeBase
from glasslab.config import current_settings
from glasslab.utils.datatypes.genome_reference import Chromosome,\
    SequenceTranscriptionRegion, SequenceDetail
from glasslab.glassatlas.datatypes.metadata import SequencingRun
from matplotlib import pyplot
import os, sys

class LinearGrapher(object):
    output_dir = None
    
    # Regions are chr_id, start, end
    regions_test = [(10, 79342169, 80913010),]
    regions = [# Chrom 19
                (10, 79342169, 80913010),
                (10, 80916060, 81436260),
                (17, 54279912, 55926251),
                (8,  3050237, 4485013),
                (17, 32046187, 32444478),
                (9,  18299588, 22016296),
                (8,  82850819, 84386422),
                (17, 30830908, 31636881),
                (8,  71067611, 71834509),
                (8,  70302178, 70771910),
                (8,  68813131, 69942927),
                (7,  28430896, 28923864),
                (7,  29042107, 29983965),
                (7,  21648006, 28147390),
                (7,  21429589, 21637007),
                (7,  18731717, 21182957),
                (7,  16238643, 16924171),
                (7,  10516719, 16080268),
                (7,  31909600, 34591777),
                (7,  3714036, 8792717),
                # Chrom 21
                (16, 76009752, 98953569),
                (17, 29668636, 30821215),
                (10, 76004461, 78264167),]
    
    regions = [# Chrom 19
                (10, 69342169, 70913010),
                (10, 40916060, 41436260),
                (17, 24279912, 25926251),
                (8,  6050237, 7485013),
                (17, 12046187, 12444478),
                (9,  28299588, 32016296),
                (8,  62850819, 64386422),
                (17, 40830908, 41636881),
                (8,  51067611, 51834509),
                (8,  72302178, 72771910),
                (8,  65813131, 66942927),
                (7,  27430896, 27923864),
                (7,  30042107, 30983965),
                (7,  11648006, 18147390),
                (7,  11429589, 11637007),
                (7,  8731717, 11182957),
                (7,  6238643, 6924171),
                (7,  20516719, 26080268),
                (7,  41909600, 44591777),
                (7,  33714036, 38792717),
                # Chrom 21
                (16, 56009752, 78953569),
                (17, 19668636, 20821215),
                (10, 56004461, 58264167),]
    
    cell_base = CellTypeBase().get_cell_type_base(current_settings.CURRENT_CELL_TYPE)()
    transcript_model = cell_base.glass_transcript
    
    # Specific parameters
    timepoint = '1h'
    bar_height = 1
    bar_margin = .1
    colors = ['blue', 'green']
    
    def __init__(self, output_dir):
        self.output_dir = output_dir
        
    def graph_regions(self):
        for region in self.regions:
            self.graph_region(*region)
            
    def graph_region(self, chr_id, start, end):
        states = ('down',False,'up')
        
        # Create graph
        fig = pyplot.figure(figsize=(12,6))
        ax = fig.add_subplot(111)
        ax.set_title('KLA induction at %s in Mouse Chr %d, %d - %d' % (self.timepoint, chr_id, start, end))
        ax.set_xlim(start - 1, end + 1)
        ax.set_xlabel('Position on Chr %d' % chr_id)
        
        tick_labels = []
        tick_pos = []
        # Get Transcripts of interest
        for i, induction_state in enumerate(states):
            row = 2*i
            for strand in (0, 1):
                tick_label = (induction_state and '2x ' + induction_state or 'No ind.') + (strand and ' -' or ' +')
                tick_labels.append(tick_label)
                transcripts = self.get_transcripts(chr_id, start, end, strand, 
                                                   kla_induced=induction_state, timepoint=self.timepoint)
                # Add transcript
                xranges = [(t.transcription_start, t.transcription_end - t.transcription_start + 1)
                            for t in transcripts]
                ymin = .25 + (row + strand)*self.bar_height + (row + strand)*self.bar_margin
                yranges = (ymin, self.bar_height)
                tick_pos.append(ymin + .5* self.bar_height)
                ax.broken_barh(xranges, yranges, facecolors=self.colors[strand])
        
        ax.set_yticklabels(tick_labels)
        ax.set_yticks(tick_pos)
        pyplot.savefig(os.path.join(self.output_dir,'chr_%d_from_%d_to_%d.png' % (chr_id, start, end)))

            
        
    def get_transcripts(self, chr_id, start, end, strand, kla_induced=False, timepoint='1h'):
        '''
        Get transcripts corresponding to the region passed. 
        Filter according to KLA profile and timepoint.
        
        Note that kla_induced=None means both induced and not induced;
        kla_induced=False means specifically those transcripts that are not 2x induced.
        kla_induced=True means specifically those transcripts that are 2x induced.
        kla_induced='up' or 'down' indicates directional 2x induction.
        '''
        induction_ratio = '(sum(kla.tag_count)*(sum(notx_run.total_tags)::numeric/sum(kla_run.total_tags)::numeric))/sum(notx.tag_count)::numeric'
        
        if kla_induced is None:
            induction_condition = ''
        elif kla_induced is False:
            induction_condition = 'having %s > .5 and %s < 2' % (induction_ratio, induction_ratio)
        elif kla_induced is True:
            induction_condition = 'having %s <= .5 or %s >= 2' % (induction_ratio, induction_ratio)
        elif kla_induced is 'up':
            induction_condition = 'having %s >= 2' % induction_ratio
        elif kla_induced is 'down':
            induction_condition = 'having %s <= .5' % induction_ratio
        
        transcripts = self.transcript_model.objects.raw(
                '''
                 select t1.id, t1.chromosome_id, t1.strand, t1.transcription_start, t1.transcription_end, t1.start_end, t1.score, 
                        round((sum(kla.tag_count)*(sum(notx_run.total_tags)::numeric/sum(kla_run.total_tags)::numeric))/sum(notx.tag_count)::numeric, 3) as kla_fc,
                        seq.gene_names
                from 
                "%s" t1

                left outer join (SELECT seq.glass_transcript_id, array_agg(distinct trim(det.gene_name)) as gene_names 
                    FROM "%s" seq
                    join "%s" reg
                    on seq.sequence_transcription_region_id = reg.id
                
                    join "%s" det
                    on reg.sequence_identifier_id = det.sequence_identifier_id
                    
                    group by seq.glass_transcript_id
                    ) seq
                on t1.id = seq.glass_transcript_id
                
                join "%s" notx
                on t1.id = notx.glass_transcript_id
                join "%s" notx_run
                on notx.sequencing_run_id = notx_run.id
                    
                join "%s" kla
                on t1.id = kla.glass_transcript_id
                join "%s" kla_run
                on kla.sequencing_run_id = kla_run.id
                
                    
                WHERE score >= 15
                    AND chromosome_id=%d 
                    AND start_end && public.make_box(%d,0,%d,0)
                    AND strand = %d
                    AND notx_run.standard = true
                    AND notx_run.wt = true
                    AND notx_run.notx = true
                    AND notx_run.other_conditions = false
                    AND notx_run.timepoint = '%s'
                    AND kla_run.standard = true
                    AND kla_run.wt = true
                    AND kla_run.kla = true
                    AND kla_run.other_conditions = false
                    AND kla_run.timepoint = '%s'
                GROUP BY t1.id, t1.strand, t1.transcription_start, t1.transcription_end, t1.start_end, t1.score, 
                    t1.chromosome_id, seq.gene_names
                %s
                ORDER BY t1.transcription_start ASC
                ''' % (self.transcript_model._meta.db_table,
                       self.cell_base.glass_transcript_sequence._meta.db_table,
                       SequenceTranscriptionRegion._meta.db_table,
                       SequenceDetail._meta.db_table,
                       self.cell_base.glass_transcript_source._meta.db_table,
                       SequencingRun._meta.db_table,
                       self.cell_base.glass_transcript_source._meta.db_table,
                       SequencingRun._meta.db_table,
                       chr_id, start, end, strand, timepoint, timepoint,
                       induction_condition
                       )
                )
        
        return transcripts
    
if __name__ == '__main__':
    output_dir = len(sys.argv) > 1 and sys.argv[1] or '/Users/karmel/Desktop/Projects/GlassLab/Notes and Reports/Syntenic regions/Linear Graphs Shifted/'
    grapher = LinearGrapher(output_dir)
    grapher.graph_regions()
    