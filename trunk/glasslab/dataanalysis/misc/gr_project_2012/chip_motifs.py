'''
Created on Jul 5, 2012

@author: karmel
'''
from glasslab.dataanalysis.motifs.motif_analyzer import MotifAnalyzer
from glasslab.dataanalysis.misc.gr_project_2012.elongation import get_rep_string
import sys


if __name__ == '__main__':
    yzer = MotifAnalyzer()
    
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/motifs'
    dirpath = yzer.get_path(dirpath)
    
    grouped = yzer.import_file(yzer.get_filename(dirpath, 'feature_vectors.txt'))
    
    trans, up_in_kla = [], []
    if True:
        # Minimal ratio in KLA+Dex vs. KLA pausing
        try: min_ratio= float(sys.argv[1])
        except IndexError: min_ratio = -1
        try: 
            try: secondary_min_ratio= float(sys.argv[2])
            except ValueError: secondary_min_ratio= sys.argv[2]
        except IndexError: secondary_min_ratio = 'none'
        try: thresh = int(sys.argv[3])
        except IndexError: thresh = 2
        
        grouped['relevant_sets'] = 0
        grouped['kla_relevant_sets'] = 0
        
        rep_ids = (1, 2, 3, 4)
        for replicate_id in rep_ids:
            rep_str = get_rep_string(replicate_id)
            
            
            primary_min = grouped['kla_{0}gene_body_lfc'.format(rep_str)] >= min_ratio
            
            if secondary_min_ratio != 'none':
                secondary_min = grouped['dex_over_kla_{0}gene_body_lfc'.format(rep_str)] <= secondary_min_ratio
            else: 
                secondary_min = True
            
            up_set = grouped.ix[primary_min]['glass_transcript_id'].values.tolist()
            trans_set = grouped.ix[primary_min & secondary_min]['glass_transcript_id'].values.tolist()
            grouped['relevant_sets'] += (primary_min & secondary_min).apply(int)
            grouped['kla_relevant_sets'] += (primary_min).apply(int)
            
            trans.append(trans_set)
            up_in_kla.append(up_set)
            
            print 'Genes with rep {0} KLA LFC >= {1}:'.format(
                                    replicate_id, min_ratio), len(up_set)
            
            print 'Genes with rep {0} KLA LFC >= {1} and Dex over KLA LFC <= {2}:'.format(
                                    replicate_id, min_ratio, secondary_min_ratio), len(trans_set)
            
            
        
        
        for x in xrange(1,5):
            print 'Up in KLA in at least {0} reps:'.format(x), sum(grouped['kla_relevant_sets'] >= x)
            print 'Transrepressed in at least {0} reps:'.format(x), sum(grouped['relevant_sets'] >= x)
        
        
        # For motif finding
        # Peak files with transcripts
        motif_dirpath = yzer.get_filename(dirpath, 'from_peaks','motifs_h3k4me2_nfr_gene_body/')
        filename = yzer.get_filename(dirpath, 'from_peaks', 'h3k4me2_nfr_vectors.txt')
        
        data = yzer.import_file(filename)
        data = data.fillna(0)
        #data['id'] = data['peak_id']
        
        relevant_ids = grouped[grouped['relevant_sets'] >= thresh]['glass_transcript_id']
        kla_relevant_ids = grouped[grouped['kla_relevant_sets'] >= thresh]['glass_transcript_id']
    
        if True:
            for name, dataset in (('all', data[data['glass_transcript_id'].isin(grouped['glass_transcript_id'])],),
                                  ('up_in_kla', data[data['glass_transcript_id'].isin(kla_relevant_ids)],),
                                  ('transrepressed', data[data['glass_transcript_id'].isin(relevant_ids)],),
                                  ):
                curr_path = yzer.get_and_create_path(motif_dirpath, name)
                yzer.prep_files_for_homer(dataset, '{0}_kla_{1}_dex_over_kla_{2}_thresh_{3}_transcripts'.format(
                                                name, min_ratio, secondary_min_ratio, thresh), curr_path, 
                                          center=True, reverse=False, preceding=False, size=200)
                