'''
Created on Jul 2, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.misc.gr_project_2012.elongation import draw_elongation_profile,\
    get_rep_string, set_up_sequencing_run_ids
from glasslab.dataanalysis.graphing.basepair_counter import BasepairCounter
import os

def get_tag_proportions(all_data, subset, subset_label):
    
    for label, data in (('All',all_data), (subset_label,subset)):
        total_tags = sum(data['tag_count'])
        print 'Total tags in {0}: {1}'.format(label, total_tags)
        
        states = (('KLA','kla_{0}state'), ('KLA+Dex','kla_dex_{0}state'),
                  ('KLA+Dex over KLA','dex_over_kla_{0}state'),)
        for desc,state in states:
            for replicate_id in ('',1,2,3,4):
                rep_str = get_rep_string(replicate_id)
                state_str = state.format(rep_str)
                datasets = [('No change in {0}'.format(desc), data[data[state_str] == 0]),
                            ('Up in {0}'.format(desc), data[data[state_str] == 1]),
                            ('Down in {0}'.format(desc), data[data[state_str] == -1]),
                            ('Up > 2x in KLA, Down > 1.5x from that in Dex', 
                             data[(data['kla_{0}state'.format(rep_str)] == 1)
                                  & (data['dex_over_kla_{0}state'.format(rep_str)] == -1)]),]
                for name, dataset in datasets:
                    dataset_tags = sum(dataset['total_tags'])
                    print 'Total tags in {0}: {1}'.format(name, dataset_tags)
                    print 'Percent of total tags in {0}: {1}'.format(name, dataset_tags/total_tags)
            
        
if __name__ == '__main__':
    
    grapher = BasepairCounter()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/basepair_buckets'
    dirpath = grapher.get_path(dirpath)
    
    if True:
        filename = grapher.get_filename(dirpath, 'refseq_by_bucket.txt')
        data = grapher.import_file(filename)
        
        run_ids = set_up_sequencing_run_ids()
    
        def bucket_score(group):
            # Ratio of starts in between -20 and 249 bp
            return len(group[(group['bucket'] >= 17) & (group['bucket'] <= 25)])/len(group)
        
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
        # Hardcoding 2500 here because that's what I used in the SQL query
        data['basepair'] = data['bucket']*int((2500 - grapher.from_bp)/100) + grapher.from_bp
        
        # Create filtered groups.
        datasets = [#('not_paused_dmso_15', data[data['dmso_bucket_score'] <= .15]),
                    #('not_paused_kla_15', data[data['kla_bucket_score'] <= .15]),
                    #('not_paused_kla_dex_15', data[data['kla_dex_bucket_score'] <= .15]),
                    ('all_refseq', data),
                    ('kla_dex_more_paused_than_kla_01', 
                        data[data['kla_dex_bucket_score'] - data['kla_bucket_score'] >= .01 ]),
                    
                    ('kla_dex_more_paused_than_kla_1_01', 
                        data[data['kla_dex_1_bucket_score'] - data['kla_1_bucket_score'] >= .01 ]),
                    ('kla_dex_more_paused_than_kla_2_01', 
                        data[data['kla_dex_2_bucket_score'] - data['kla_2_bucket_score'] >= .01 ]),
                    ('kla_dex_more_paused_than_kla_3_01', 
                        data[data['kla_dex_3_bucket_score'] - data['kla_3_bucket_score'] >= .01 ]),
                    ('kla_dex_more_paused_than_kla_4_01', 
                        data[data['kla_dex_4_bucket_score'] - data['kla_4_bucket_score'] >= .01 ]),
                    
                    ]
        

        for name, dataset in datasets:
            get_tag_proportions(data, dataset, name)
            
            '''
            curr_dirpath = grapher.get_filename(dirpath, name)
            if not os.path.exists(curr_dirpath): os.mkdir(curr_dirpath)
            
            draw_elongation_profile(dataset, grapher, curr_dirpath, 
                                    show_moving_average=False, show_count=True)
    
            '''
            
        