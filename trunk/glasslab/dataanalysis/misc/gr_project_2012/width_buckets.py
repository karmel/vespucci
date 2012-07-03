'''
Created on Jul 2, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.misc.gr_project_2012.elongation import draw_elongation_profile,\
    get_rep_string, set_up_sequencing_run_ids
from glasslab.dataanalysis.graphing.basepair_counter import BasepairCounter
import os
from matplotlib import pyplot

def draw_boxplot(data, label, dirpath):
    
    curr_dirpath = grapher.get_filename(dirpath, 'boxplots_{0}'.format(label))
    if not os.path.exists(curr_dirpath): os.mkdir(curr_dirpath)
    
    # Group and take mean. We can use mean because we only care
    # about the values that are the same for all rows for a given transcript.
    data = data.groupby('glass_transcript_id',as_index=False).mean()    
    states = (('KLA','kla_{0}state'), ('KLA+Dex','kla_dex_{0}state'),
              ('KLA+Dex over KLA','dex_over_kla_{0}state'),)
    for desc,state in states:
        
        for replicate_id in ('',1,2,3,4):
            rep_str = get_rep_string(replicate_id)
            state_str = state.format(rep_str)
            datasets = [('No change', data[data[state_str] == 0]),
                        ('Up >= 2x', data[data[state_str] == 1]),
                        ('Down >= 2x', data[data[state_str] == -1]),]

            bar_names, datasets = zip(*datasets)
            pausing_ratios = [d['kla_dex_{0}bucket_score'.format(rep_str)] - d['kla_{0}bucket_score'.format(rep_str)]
                                for d in datasets]
            
            ax = grapher.boxplot(pausing_ratios, 
                            bar_names, 
                            title='Pausing Ratio Delta in {0}, {1}'.format(
                                        desc, (replicate_id and 'Group {0}'.format(replicate_id) or 'Overall')), 
                            xlabel='State in {0} {1}'.format(desc, replicate_id), 
                            ylabel='Pausing ratio delta: (KLA+Dex pausing ratio) - (KLA pausing ratio)', 
                            show_outliers=False, show_plot=False)
            
            pyplot.text(.05, .9, 'Total transcripts: {0}'.format(len(data)), transform=ax.transAxes)
            grapher.save_plot(grapher.get_filename(curr_dirpath, 'boxplot_{0}.png'.format(state_str)))
            
def get_tag_proportions(data, label):
    
    
    total_trans = len(set(data['glass_transcript_id']))
    print '\n\n\nTotal transcripts in {0}:\t{1}'.format(label, total_trans)
    
    states = (('KLA','kla_{0}state'), ('KLA+Dex','kla_dex_{0}state'),
              ('KLA+Dex over KLA','dex_over_kla_{0}state'),)
    for desc,state in states:
        for replicate_id in ('',1,2,3,4):
            rep_str = get_rep_string(replicate_id)
            state_str = state.format(rep_str)
            if desc == 'KLA':
                datasets = [('Down > 1.5x in Dex over KLA {0}'.format(replicate_id), 
                             data[(data['dex_over_kla_{0}state'.format(rep_str)] == -1)]),
                            ('Up > 2x in KLA, Down > 1.5x from that in Dex {0}'.format(replicate_id), 
                             data[(data['kla_{0}state'.format(rep_str)] == 1)
                                  & (data['dex_over_kla_{0}state'.format(rep_str)] == -1)]),
                            ('Down > 2x in KLA, No change in Dex {0}'.format(replicate_id), 
                             data[(data['kla_{0}state'.format(rep_str)] == -1)
                                  & (data['dex_over_kla_{0}state'.format(rep_str)] == 0)]),
                            ('Down > 2x in KLA, Up > 1.5x in Dex {0}'.format(replicate_id), 
                             data[(data['kla_{0}state'.format(rep_str)] == -1)
                                  & (data['dex_over_kla_{0}state'.format(rep_str)] == 1)]),
                            ('Down > 2x in KLA, Down > 1.5x in Dex {0}'.format(replicate_id), 
                             data[(data['kla_{0}state'.format(rep_str)] == -1)
                                  & (data['dex_over_kla_{0}state'.format(rep_str)] == -1)]),
                            ]
            else: datasets = []
            datasets += [('No change in {0} {1}'.format(desc, replicate_id), data[data[state_str] == 0]),
                        ('Up in {0} {1}'.format(desc, replicate_id), data[data[state_str] == 1]),
                        ('Down in {0} {1}'.format(desc, replicate_id), data[data[state_str] == -1]),]
            for name, dataset in datasets:
                dataset_trans = len(set(dataset['glass_transcript_id']))
                print 'Total transcripts in {0}:\t{1}'.format(name, dataset_trans)
                print 'Percent of transcripts in {0}:\t{1}'.format(name, dataset_trans/total_trans)
        
        
if __name__ == '__main__':
    
    grapher = BasepairCounter()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/buckets_per_row'
    dirpath = grapher.get_path(dirpath)
    
    if True: 
        filename = grapher.get_filename(dirpath, 'refseq_by_transcript_and_bucket.txt')
        data = grapher.import_file(filename)
        
        run_ids = set_up_sequencing_run_ids()
    
        def bucket_score(group):
            # Ratio of starts in between 0 and 249 bp to rest of gene
            try: 
                return sum(group[group['bucket'] == 3]['tag_count'])/sum(group[group['bucket'] >= 3]['tag_count'])
            except ZeroDivisionError: return 0
        
        # For each sequencing run group, fill in the bucket score val
        for run_type, id_set in run_ids.iteritems():
            for replicate_id in ('',1,2,3,4):
                rep_str = get_rep_string(replicate_id)
                curr_ids = id_set[replicate_id or 0]
                # First subset rows by sequencing run_ids of interest
                subset = data[data['sequencing_run_id'].isin(curr_ids)]
                # Group by transcript, and assign bucket score to each row
                grouped = subset.groupby('glass_transcript_id')
                grouped = grouped.apply(bucket_score)
                # Fill in bucket score for each original row.
                data['{0}_{1}bucket_score'.format(run_type, rep_str)] = grouped[data['glass_transcript_id']].values
            
            
        
        # For the sake of graphing, imitate basepair
        data['basepair'] = data['bucket']*int((grapher.to_bp - grapher.from_bp)/100) + grapher.from_bp
        
        # Create filtered groups.
        datasets = [#('not_paused_dmso_15', data[data['dmso_bucket_score'] <= .15]),
                    #('not_paused_kla_15', data[data['kla_bucket_score'] <= .15]),
                    #('not_paused_kla_dex_15', data[data['kla_dex_bucket_score'] <= .15]),
                    ('all_refseq', data),
                    ('with_gr_kla_dex', data[data['gr_kla_dex'] == 1]),
                    ('with_p65_kla_dex', data[data['p65_kla_dex'] == 1]),
                    ('with_p65_no_gr_kla_dex', data[(data['p65_kla_dex'] == 1) & (data['gr_kla_dex'] == 0)]),
                    ('with_gr_no_p65_kla_dex', data[(data['p65_kla_dex'] == 0) & (data['gr_kla_dex'] == 1)]),
                    ('with_gr_and_p65_kla_dex', data[(data['p65_kla_dex'] == 1) & (data['gr_kla_dex'] == 1)]),
                    ]
        '''
                    ('kla_dex_more_paused_than_kla_05', 
                        data[data['kla_dex_bucket_score'] - data['kla_bucket_score'] >= .05 ]),
                    
                    ('kla_dex_more_paused_than_kla_1_05', 
                        data[data['kla_dex_1_bucket_score'] - data['kla_1_bucket_score'] >= .05 ]),
                    ('kla_dex_more_paused_than_kla_2_05', 
                        data[data['kla_dex_2_bucket_score'] - data['kla_2_bucket_score'] >= .05 ]),
                    ('kla_dex_more_paused_than_kla_3_05', 
                        data[data['kla_dex_3_bucket_score'] - data['kla_3_bucket_score'] >= .05 ]),
                    ('kla_dex_more_paused_than_kla_4_05', 
                        data[data['kla_dex_4_bucket_score'] - data['kla_4_bucket_score'] >= .05 ]),
                    
                    ]
        '''
        for name, dataset in datasets:
            #get_tag_proportions(dataset, name)
            draw_boxplot(dataset, name, dirpath)
            '''
            curr_dirpath = grapher.get_filename(dirpath, name)
            if not os.path.exists(curr_dirpath): os.mkdir(curr_dirpath)
            
            draw_elongation_profile(dataset, grapher, curr_dirpath, 
                                    show_moving_average=False, show_count=True)
    
            '''
            