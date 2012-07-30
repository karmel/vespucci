'''
Created on Jun 25, 2012

@author: karmel
'''
from glasslab.dataanalysis.motifs.motif_analyzer import MotifAnalyzer

if __name__ == '__main__':
    yzer = MotifAnalyzer()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/GR chip/'
    dirpath = yzer.get_path(dirpath)
    
    
    if False:
        # Peak files with transcripts
        motif_dirpath = yzer.get_filename(dirpath, 'motifs_gr_kla_dex_promoters/')
        filename = yzer.get_filename(dirpath, 'p65_kla_dex_vectors_promoters.txt')
        
        data = yzer.import_file(filename)
        data = data.fillna(0)
        data['id'] = data['peak_id']
        #data = data[data['p65_kla_dex_tag_count'] < data['p65_kla_tag_count']]    
        for name, dataset in (('all', data,),
                              ('up_in_kla', data[(data['kla_lfc'] >= 1)],),
                              ('up_in_kla_1', data[(data['kla_1_lfc'] >= 1)],),
                              ('up_in_kla_2', data[(data['kla_2_lfc'] >= 1)],),
                              ('up_in_kla_3', data[(data['kla_3_lfc'] >= 1)],),
                              ('up_in_kla_4', data[(data['kla_4_lfc'] >= 1)],),
                              ('transrepressed', data[(data['kla_lfc'] >= 1) & (data['dex_over_kla_lfc'] <= -.58)],),
                              ('transrepressed_1', data[(data['kla_1_lfc'] >= 1) & (data['dex_over_kla_1_lfc'] <= -.58)],),
                              ('transrepressed_2', data[(data['kla_2_lfc'] >= 1) & (data['dex_over_kla_2_lfc'] <= -.58)],),
                              ('transrepressed_3', data[(data['kla_3_lfc'] >= 1) & (data['dex_over_kla_3_lfc'] <= -.58)],),
                              ('transrepressed_4', data[(data['kla_4_lfc'] >= 1) & (data['dex_over_kla_4_lfc'] <= -.58)],),
                              ('transrepressed_union', data[((data['kla_1_lfc'] >= 1) & (data['dex_over_kla_1_lfc'] <= -.58)) 
                                                            | ((data['kla_2_lfc'] >= 1) & (data['dex_over_kla_2_lfc'] <= -.58))
                                                            | ((data['kla_3_lfc'] >= 1) & (data['dex_over_kla_3_lfc'] <= -.58)) 
                                                            | ((data['kla_4_lfc'] >= 1) & (data['dex_over_kla_4_lfc'] <= -.58))
                                                            ],),
                              ('up_in_kla_union', data[((data['kla_1_lfc'] >= 1)) | ((data['kla_2_lfc'] >= 1)) 
                                                       | ((data['kla_3_lfc'] >= 1)) | ((data['kla_4_lfc'] >= 1))
                                                            ],),
                              
                              ):
            curr_path = yzer.get_and_create_path(motif_dirpath, name)
            yzer.prep_files_for_homer(dataset, '{0}_transcripts'.format(name), curr_path, 
                                      center=True, reverse=False, preceding=False, size=200)
            yzer.prep_files_for_homer(dataset[dataset['distal'] == 't'], '{0}_distal'.format(name), curr_path, 
                                      center=True, reverse=False, preceding=False, size=200)
            yzer.prep_files_for_homer(dataset[dataset['refseq'] == 't'], '{0}_refseq'.format(name), curr_path, 
                                      center=True, reverse=False, preceding=False, size=200)
    if False:
        # For peak files, no transcripts
        motif_dirpath = yzer.get_filename(dirpath, 'motifs_p65_kla_outer_join_p65_kla_dex/')
        filename = yzer.get_filename(dirpath, 'p65_kla_outer_join_p65_kla_dex.txt')
        
        data = yzer.import_file(filename)
        data = data.fillna(0)
        data['id'] = data['p1_id']
        data['transcription_start'] = data['p1_start']
        data['transcription_end'] = data['p1_end']
        data['strand'] = 0
        for name, dataset in (('all', data,),
                              ('less_in_kla_dex', data[(data['p1_tag_count'] > data['p2_tag_count'])],),
                              ('less_in_kla_dex_with_gr', data[(data['p1_tag_count'] > data['p2_tag_count'])
                                                            & (data['p3_tag_count'] > 0)],),
                              ):
            curr_path = yzer.get_and_create_path(motif_dirpath, name)
            yzer.prep_files_for_homer(dataset, '{0}_peaks'.format(name), curr_path, 
                                      center=True, reverse=False, preceding=False, size=200)
            
    if True:
        # Peak files with transcripts
        motif_dirpath = yzer.get_filename(dirpath, 'motifs_gr_kla_dex_up/')
        filename = yzer.get_filename(dirpath, 'gr_kla_dex_vectors.txt')
        
        data = yzer.import_file(filename)
        data = data.fillna(0)
        data['id'] = data['peak_id']
        #data = data[data['p65_kla_dex_tag_count'] < data['p65_kla_tag_count']]    
        for name, dataset in (('all', data,),
                              ('up_in_kla_dex', data[(data['dex_over_kla_lfc'] >= 1)],),
                              ('up_in_kla_dex_1', data[(data['dex_over_kla_1_lfc'] >= 1)],),
                              ('up_in_kla_dex_2', data[(data['dex_over_kla_2_lfc'] >= 1)],),
                              ('up_in_kla_dex_3', data[(data['dex_over_kla_3_lfc'] >= 1)],),
                              ('up_in_kla_dex_4', data[(data['dex_over_kla_4_lfc'] >= 1)],),
                              ('up_in_kla_dex_union', data[((data['dex_over_kla_1_lfc'] >= 1)) | ((data['dex_over_kla_2_lfc'] >= 1)) 
                                                       | ((data['dex_over_kla_3_lfc'] >= 1)) | ((data['dex_over_kla_4_lfc'] >= 1))
                                                            ],),
                              
                              ):
            curr_path = yzer.get_and_create_path(motif_dirpath, name)
            yzer.prep_files_for_homer(dataset, '{0}_transcripts'.format(name), curr_path, 
                                      center=True, reverse=False, preceding=False, size=200)
            yzer.prep_files_for_homer(dataset[dataset['distal'] == 't'], '{0}_distal'.format(name), curr_path, 
                                      center=True, reverse=False, preceding=False, size=200)
            yzer.prep_files_for_homer(dataset[dataset['refseq'] == 't'], '{0}_refseq'.format(name), curr_path, 
                                      center=True, reverse=False, preceding=False, size=200)
    