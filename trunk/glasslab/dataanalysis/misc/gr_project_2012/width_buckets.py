'''
Created on Jul 2, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.misc.gr_project_2012.elongation import draw_elongation_profile,\
    get_rep_string, set_up_sequencing_run_ids
from glasslab.dataanalysis.graphing.basepair_counter import BasepairCounter
import os

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
        data['basepair'] = data['bucket']*int((grapher.to_bp - grapher.from_bp)/100) + grapher.from_bp
        
        # Create filtered groups.
        datasets = [('paused_dmso_33', data[data['dmso_bucket_score'] >= .33]),
                    ('paused_kla_33', data[data['kla_bucket_score'] >= .33]),
                    ('paused_kla_dex_33', data[data['kla_dex_bucket_score'] >= .33]),
                    ]
        
        print len(data[data['dmso_bucket_score'] >= .33])
        print data['dmso_bucket_score']
        for name, dataset in datasets:
            curr_dirpath = grapher.get_filename(dirpath, name)
            if not os.path.exists(curr_dirpath): os.mkdir(curr_dirpath)
            
            draw_elongation_profile(dataset, grapher, curr_dirpath, show_moving_average=False)
    
            
            
        