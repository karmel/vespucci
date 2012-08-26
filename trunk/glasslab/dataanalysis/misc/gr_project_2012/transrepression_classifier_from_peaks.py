'''
Created on Jul 4, 2012

@author: karmel

The goal here is to see if we can tease out which features are 
predictive of characteristics of interest, such as pausing ratio
or transrepression. Worth a stab.
'''
from __future__ import division
from glasslab.dataanalysis.machinelearning.logistic_classifier import LogisticClassifier
import os
import sys


class TransrepressionClassifier(LogisticClassifier):
    
    def custom_clean(self, transcripts, peaks):
        # Distch some redundant/unnecessary columns
        transcripts = transcripts.drop(['ucsc_link_nod','id','transcription_start','transcription_end',
                                        'distal','refseq','strand','chr_name',], axis=1)
        # Then merge data
        # This gives us multiple rows per glass_transcript_id. 
        data = peaks.merge(transcripts, how='outer',on='glass_transcript_id')
        
        for x in xrange(2,9):
            data['no_peak_{0}'.format(x)] = data['tag_count_{0}'.format(x)].isnull().apply(int)
            
        data = data.fillna(1) # To make division easier
        
        # We want ratios between pairs of peaks
        # GR kla_dex/dex
        def replace_0(x): return max(1,x)
        data['gr_kla_dex_over_dex'] = data['tag_count'].apply(replace_0)/data['tag_count_2'].apply(replace_0)
        data['p65_kla_dex_over_kla'] = data['tag_count_3'].apply(replace_0)/data['tag_count_4'].apply(replace_0)
        data['pu_1_kla_dex_over_kla'] = data['tag_count_5'].apply(replace_0)/data['tag_count_6'].apply(replace_0)
        data['stat1_ifng_over_notx'] = data['tag_count_7'].apply(replace_0)/data['tag_count_8'].apply(replace_0)
        
        
        return data
        
        
if __name__ == '__main__':
    learner = TransrepressionClassifier()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/classification/from_peaks'
    dirpath = learner.get_path(dirpath)
    
    transcripts = learner.import_file(learner.get_filename(dirpath, 'transcript_vectors_kla_1_dex_over_kla_-0_58.txt'))
    peaks = learner.import_file(learner.get_filename(dirpath, 'gr_kla_dex_vectors_with_peaks.txt'))
    
    data = learner.custom_clean(transcripts, peaks)
    
    
    if False:
        # Output some gene lists.
        transcripts['gene_names'] = transcripts['gene_names'].apply(lambda x: x.strip('{').strip('}'))
        sub_trans = transcripts[transcripts['relevant_sets'] >= 2]
        sub_trans = sub_trans.sort(columns=['relevant_sets','gene_names'], ascending=False)
        sub_trans.to_csv(learner.get_filename(dirpath,'transrepressed_genes.txt'), sep='\t',  
                           cols=['glass_transcript_id', 'chr_name', 'transcription_start', 'transcription_end', 
                               'strand', 'gene_names', 'relevant_sets', 'kla_relevant_sets', 'length',  
                               'refseq', 'distal', 'transcript_score', 'has_infrastructure', 
                               'gr_dex_tag_count', 'gr_kla_dex_tag_count', 'p65_kla_tag_count',
                               'p65_kla_dex_tag_count', 'kla_lfc', 'kla_1_lfc', 'kla_2_lfc', 'kla_3_lfc', 
                               'kla_4_lfc', 'kla_dex_lfc', 'kla_dex_1_lfc', 'kla_dex_2_lfc', 'kla_dex_3_lfc', 
                               'kla_dex_4_lfc', 'dex_over_kla_lfc', 'dex_over_kla_1_lfc', 'dex_over_kla_2_lfc', 
                               'dex_over_kla_3_lfc', 'dex_over_kla_4_lfc', 'dmso_tag_count', 'dmso_1_tag_count', 
                               'dmso_2_tag_count', 'dmso_3_tag_count', 'dmso_4_tag_count', 'kla_tag_count', 
                               'kla_1_tag_count', 'kla_2_tag_count', 'kla_3_tag_count', 'kla_4_tag_count', 
                               'kla_dex_tag_count', 'kla_dex_1_tag_count', 'kla_dex_2_tag_count', 
                               'kla_dex_3_tag_count', 'kla_dex_4_tag_count'], header=True, index=False)
    
    if False:
        # How about transrepression or derepression?
        try: force_choice = sys.argv[1].lower() == 'force'
        except IndexError: force_choice = False
        try: extra_dir = sys.argv[2]
        except IndexError: extra_dir = ''
        try: thresh = int(sys.argv[3])
        except IndexError: thresh = 2
        
        subdir = learner.get_filename(dirpath, 
                    'transrepressed' + '_' + extra_dir)
        if force_choice: subdir = subdir + '_forced_choice'
        
        if not os.path.exists(subdir): os.makedirs(subdir)
        
        data = data[data['distance_to_tss'] <= 100]
        data = data[data['kla_relevant_sets'] >= 2]
            
        if False: 
            means = data.groupby(['glass_transcript_id','chr_name'],as_index=False).mean()
            data = data.groupby(['glass_transcript_id','chr_name'],as_index=False).sum()
            
            labels = (means['relevant_sets'] >= thresh).apply(int)
        else:
            labels = (data['relevant_sets'] >= thresh).apply(int)
            
        # Get rid of lfc columns    
        dataset = data.filter(regex=r'(?!(.*_lfc|.*_tag_count|.*relevant_sets|.*transcription|.*score|.*id))')
        
        
        dataset = learner.make_numeric(dataset)
        dataset = learner.normalize_data(dataset)
    
        
        best_err = 1.0
        best_c = 0
        best_chosen = []
        possible_k = [20, 10, 5, 2]
        for k in possible_k:
            if force_choice:
                chosen = ['tag_count_3', 'tag_count_4']
                #chosen = ['kla_{0}bucket_score'.format(rep_str), 'tag_count']
            else:
                chosen = learner.get_best_features(dataset, labels, k=k)
                
            num_features = len(chosen)
            
            err, c = learner.run_nested_cross_validation(dataset, labels, columns=chosen,
                        draw_roc=True, draw_decision_boundaries=force_choice,
                        title_suffix='Transrepressed (KLA/notx LFC >= 1, KLA+Dex/KLA <= -0.58)',
                        save_path_prefix=learner.get_filename(subdir,'plot_kla_1_dex_over_kla_-0_58'),
                    )
            
            if err < best_err:
                best_err = err
                best_c = c
                best_chosen = chosen
                
            if force_choice: break
    
        print "Best number of features: ", len(best_chosen)
        print "Best features: ", best_chosen
        print "Best C, MSE: ", best_c, best_err

        
            
        