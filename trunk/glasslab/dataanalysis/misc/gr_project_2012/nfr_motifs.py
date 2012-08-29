'''
Created on Jul 5, 2012

@author: karmel
'''
from __future__ import division
from glasslab.dataanalysis.motifs.motif_analyzer import MotifAnalyzer
from glasslab.dataanalysis.misc.gr_project_2012.elongation import get_rep_string
import sys
from matplotlib import pyplot
from random import shuffle
import pandas


if __name__ == '__main__':
    yzer = MotifAnalyzer()
    
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/motifs'
    dirpath = yzer.get_path(dirpath)
    
    if False:
        grouped = yzer.import_file(yzer.get_filename(dirpath, 'transcript_vectors.txt'))
        
        grouped['glass_transcript_id'] = grouped['id']
        
        #grouped = grouped[grouped['distal'] == 'f']
        #grouped = grouped[grouped['gr_kla_dex_tag_count'] > 0]
        grouped = grouped[grouped['has_refseq'] == 1]
        grouped = grouped[grouped['transcript_score'] >= 10]
        
        trans, up_in_kla = [], []
        if True:
            # Minimal ratio in KLA+Dex vs. KLA pausing
            try: 
                try: min_ratio= float(sys.argv[1])
                except ValueError: min_ratio= sys.argv[1]
            except IndexError: min_ratio = 1
            try: 
                try: secondary_min_ratio= float(sys.argv[2])
                except ValueError: secondary_min_ratio= sys.argv[2]
            except IndexError: secondary_min_ratio = -.58
            try: thresh = int(sys.argv[3])
            except IndexError: thresh = 4
            
            grouped['relevant_sets'] = 0
            grouped['kla_relevant_sets'] = 0
            
            rep_ids = (1, 2, 3, 4)
            for replicate_id in rep_ids:
                rep_str = get_rep_string(replicate_id)
                
                
                if min_ratio != 'none':
                    primary_min = grouped['kla_{0}lfc'.format(rep_str)] >= min_ratio
                else: primary_min = True
                
                if secondary_min_ratio != 'none':
                    secondary_min = grouped['dex_over_kla_{0}lfc'.format(rep_str)] <= secondary_min_ratio
                else: 
                    secondary_min = True
                
                up_set = min_ratio != 'none' and grouped.ix[primary_min]['id'].values.tolist() or []
                trans_set = secondary_min_ratio != 'none' and \
                    grouped.ix[primary_min & secondary_min]['id'].values.tolist()\
                    or up_set
                grouped['relevant_sets'] += (primary_min & secondary_min).apply(int)
                if min_ratio != 'none': grouped['kla_relevant_sets'] += (primary_min).apply(int)
                
                trans.append(trans_set)
                up_in_kla.append(up_set)
                
                print 'Transcripts with rep {0} KLA LFC >= {1}:'.format(
                                        replicate_id, min_ratio), len(up_set)
                
                print 'Transcripts with rep {0} KLA LFC >= {1} and Dex over KLA LFC <= {2}:'.format(
                                        replicate_id, min_ratio, secondary_min_ratio), len(trans_set)
                
            
            #grouped.to_csv(yzer.get_filename(dirpath,'transcript_vectors_kla_1_dex_over_kla_-0_58.txt'),sep='\t',index=False)
            
            for x in xrange(1,5):
                print 'Up in KLA in at least {0} reps:'.format(x), sum(grouped['kla_relevant_sets'] >= x)
                print 'Transrepressed in at least {0} reps:'.format(x), sum(grouped['relevant_sets'] >= x)
            
        else:
            grouped = yzer.import_file(yzer.get_filename(dirpath, 'transcript_vectors_kla_1_dex_over_kla_-0_58.txt'))
            
        relevant_ids = grouped[grouped['relevant_sets'] >= thresh]['id']
        kla_relevant_ids = grouped[grouped['kla_relevant_sets'] >= thresh]['id']
        distinct_kla_relevant_ids = grouped[(grouped['kla_relevant_sets'] >= thresh) \
                                            & (grouped['relevant_sets'] <= 1)]['id']
    
        
        if False:
            # p300 enrichment in any set?
            
            filename_notx = yzer.get_filename(dirpath, 'from_peaks', 'pu_1_notx_vectors.txt')
            filename_kla = yzer.get_filename(dirpath, 'from_peaks', 'pu_1_kla_vectors.txt')
            filename_kla_dex = yzer.get_filename(dirpath, 'from_peaks', 'pu_1_kla_dex_vectors.txt')
            
            data_kla = yzer.import_file(filename_kla)
            data_kla_dex = yzer.import_file(filename_kla_dex)
            data_kla = data_kla.fillna(0)
            data_kla_dex = data_kla_dex.fillna(0)
            
            data = pandas.merge(data_kla, data_kla_dex, how='outer', on='glass_transcript_id',
                                suffixes=('_kla','_kla_dex'))
            data = data.groupby(by='glass_transcript_id', as_index=False).sum()
            data['tag_count_diff'] = data['tag_count_kla_dex'] - data['tag_count_kla']
            
            
            key = 'sum_count'
            joined = grouped.merge(data, how='outer',on='glass_transcript_id')
            joined = joined.fillna(0)
            
            joined['sum_count'] = joined['gr_kla_dex_tag_count'] - joined['gr_dex_tag_count']
            joined['avg_tag_count'] = (joined['tag_count_kla'] + joined['tag_count_kla_dex'])/2
            
            trans_peaks = joined[joined['glass_transcript_id'].isin(relevant_ids)]
            up_in_kla_peaks = joined[joined['glass_transcript_id'].isin(distinct_kla_relevant_ids)]

            pyplot.hist(trans_peaks[key],bins=20)
            pyplot.show()
            
            pyplot.hist(up_in_kla_peaks[key],bins=20)
            pyplot.show()
            
            # Create a random set of same length:
            for _ in xrange(0,10):
                rand_ids = up_in_kla_peaks.index.values
                shuffle(rand_ids)
                rand_ids = rand_ids[:len(trans_peaks)]
                pyplot.hist(up_in_kla_peaks.ix[rand_ids][key],bins=20)
                pyplot.show()
            
        if False:
            # For motif finding
            # Peak files with transcripts
            motif_dirpath = yzer.get_and_create_path(dirpath, 'from_peaks','motifs_pu_1_kla/')
            
            filename = yzer.get_filename(dirpath, 'from_peaks', 'h3k4me2_nfr_vectors.txt')
            
            data = yzer.import_file(filename)
            data = data.fillna(0)
            
            for name, dataset in (('all', data[data['glass_transcript_id'].isin(grouped['id'])],),
                                  ('up_in_kla', data[data['glass_transcript_id'].isin(kla_relevant_ids)],),
                                  ('transrepressed', data[data['glass_transcript_id'].isin(relevant_ids)],),
                                  ):
                curr_path = yzer.get_and_create_path(motif_dirpath, name)
                yzer.prep_files_for_homer(dataset, '{0}_kla_{1}_dex_over_kla_{2}_thresh_{3}_transcripts'.format(
                                                name, min_ratio, secondary_min_ratio, thresh), curr_path, 
                                          center=True, reverse=False, preceding=False, size=200)
                
        if False:
            # For motif finding
            # Peak files with transcripts
            motif_dirpath = yzer.get_and_create_path(dirpath, 'from_peaks',
                                                     'motifs_gr_kla_dex_with_dex/',
                                                     'gr_kla_dex_gt_dex_2')

            
            filename = yzer.get_filename(dirpath, 'from_peaks', 'gr_kla_dex_vectors_with_peaks.txt')
            
            data = yzer.import_file(filename)
            data = data.fillna(0)
            
            data = data[data['tag_count'] >= 10]
            data = data[(data['touches'] == 't') | (data['relationship'] == 'is downstream of')]
            #data = data[(data['relationship'] == 'is downstream of')]
            
            # Filter for kla_dex > kla
            data = data[data['tag_count'] > 2*data['tag_count_2']]
            with_peaks = grouped[grouped['id'].isin(data['glass_transcript_id'])]
            
            for x in xrange(0,5):
                print 'Count with GR peaks and transrepressed in {0}: '.format(x),\
                    sum(with_peaks['relevant_sets'] >= x)
            
            print 'Avg peaks per gene: ', sum(data['glass_transcript_id'].isin(grouped['id']))/\
                sum(grouped['length'])
            print 'Avg peaks per gene up in kla: ', sum(data['glass_transcript_id'].isin(distinct_kla_relevant_ids))/\
                sum(grouped[grouped['id'].isin(distinct_kla_relevant_ids)]['length'])
            print 'Avg peaks per gene transrepressed: ', sum(data['glass_transcript_id'].isin(relevant_ids))/\
                sum(grouped[grouped['id'].isin(relevant_ids)]['length'])
            
            
            size = 200
            if False:
                for name, dataset in (('all', data[data['glass_transcript_id'].isin(grouped['id'])],),):
                    # We have multiple copies of peaks if they align to different transcripts
                    # Groupe them after selecting those that we want
                    dataset = dataset.groupby(['id','chr_name'],as_index=False).mean()
                    curr_path = yzer.get_and_create_path(motif_dirpath, name)
                    yzer.prep_files_for_homer(dataset, name, curr_path, 
                                              center=True, reverse=False, preceding=False, size=size)
            
            if True:   
                for name, dataset in (('up_in_kla', data[data['glass_transcript_id'].isin(kla_relevant_ids)],),
                                      ('transrepressed', data[data['glass_transcript_id'].isin(relevant_ids)],),
                                      ('not_transrepressed', data[data['glass_transcript_id'].isin(
                                                                grouped[grouped['relevant_sets'] <= 1]['id'])],),
                                      ):
                    # We have multiple copies of peaks if they align to different transcripts
                    # Groupe them after selecting those that we want
                    
                    dataset = dataset.groupby(['id','chr_name'],as_index=False).mean()
                    curr_path = yzer.get_and_create_path(motif_dirpath, name)
                    yzer.prep_files_for_homer(dataset, '{0}_kla_{1}_dex_over_kla_{2}_thresh_{3}_transcripts'.format(
                                                    name, min_ratio, secondary_min_ratio, thresh), curr_path, 
                                              center=True, reverse=False, preceding=False, size=size)


    if True:
        # For motif finding
        # Peak files with transcripts
        motif_dirpath = yzer.get_and_create_path(dirpath, 'from_peaks',
                                                 'motifs_p65_kla_dex/',
                                                 'no_nearby_p65_kla')

        transcripts = yzer.import_file(yzer.get_filename(dirpath, 'transcript_vectors_kla_1_dex_over_kla_-0_58.txt'))
        filename = yzer.get_filename(dirpath, 'from_peaks', 'p65_kla_dex_vectors_with_peak_distances.txt')
        
        data = yzer.import_file(filename)
        
        ids_to_avoid = data[(data['distance_to_tss_2'].isnull() == False) & (data['distance_to_peak_2'] < 400)]['id']
        
        data = data.fillna(0)
        
        data = data[data['tag_count'] >= 30]
        #data = data[(data['touches'] == 't') | (data['relationship'] == 'is downstream of')]
        #data = data[(data['distal'] == 't')]
        #data = data[(data['refseq'] == 't') & (data['score'] >= 10)]
        
        #data = data[data['tag_count_2'] < 10]
        data = data[data['id'].isin(ids_to_avoid) == False]
        
        size = 200
        if True:   
            for name, dataset in (('all', data,),
                                  #('no_nearby_p65_kla_dex', data[data['id'].isin(ids_to_avoid) == False],),
                                  ('refseq', data[(data['score'] > 10) & (data['refseq'] == 't') 
                                                  & (data['touches'] == 't') | (data['relationship'] == 'is downstream of')],),
                                  ('distal', data[(data['distal'] == 't')],),
                                  ):
                # We have multiple copies of peaks if they align to different transcripts
                curr_path = yzer.get_and_create_path(motif_dirpath, name)
                # Group them after selecting those that we want
                dataset = dataset.groupby(['id','chr_name'],as_index=False).mean()
                yzer.prep_files_for_homer(dataset, name, curr_path, 
                                          center=True, reverse=False, preceding=False, size=size)
                