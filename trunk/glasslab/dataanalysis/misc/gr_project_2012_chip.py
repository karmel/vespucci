'''
Created on Jun 25, 2012

@author: karmel
'''
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer

if __name__ == '__main__':
    yzer = TranscriptAnalyzer()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/GR chip/motifs_2012_06/vs_p65'
    dirpath = yzer.get_path(dirpath)
    filename = yzer.get_filename(dirpath, 'all_peaks.txt')
    
    data = yzer.import_file(filename)
    data = data.fillna(0)
    
    kla_gt_dex = data[data['kla_1h_dex_2h_gr_tag_count'] > 2*data['dex_2h_gr_tag_count']]
    no_dex = data[data['dex_2h_gr_tag_count'] == 0]
    
    print 'Total GR peaks: ', len(data)
    print 'Total GR peaks with p65 in kla: ', len(data[data['kla_1h_dmso_2h_p65_tag_count'] > 0])
    print 'Total GR peaks with p65 in kla+dex: ', len(data[data['kla_1h_dex_2h_p65_tag_count'] > 0])
    print 'Total GR peaks with p65 in kla+dex > kla: ', len(data[data['kla_1h_dex_2h_p65_tag_count'] > 2*data['kla_1h_dmso_2h_p65_tag_count']])

    print 'Total GR peaks where kla+dex GR > dex: ', len(kla_gt_dex)
    print 'Total GR peaks where kla+dex GR > dex with p65 in kla: ', len(kla_gt_dex[kla_gt_dex['kla_1h_dmso_2h_p65_tag_count'] > 0])
    print 'Total GR peaks where kla+dex GR > dex with p65 in kla+dex: ', len(kla_gt_dex[kla_gt_dex['kla_1h_dex_2h_p65_tag_count'] > 0])
    print 'Total GR peaks where kla+dex GR > dex with p65 in kla+dex > kla: ', len(kla_gt_dex[kla_gt_dex['kla_1h_dex_2h_p65_tag_count'] > 2*kla_gt_dex['kla_1h_dmso_2h_p65_tag_count']])
    
    print 'Total GR peaks with no dex: ', len(no_dex)
    print 'Total GR peaks with no dex with p65 in kla: ', len(no_dex[no_dex['kla_1h_dmso_2h_p65_tag_count'] > 0])
    print 'Total GR peaks with no dex with p65 in kla+dex: ', len(no_dex[no_dex['kla_1h_dex_2h_p65_tag_count'] > 0])
    print 'Total GR peaks with no dex with p65 in kla+dex > kla: ', len(no_dex[no_dex['kla_1h_dex_2h_p65_tag_count'] > 2*no_dex['kla_1h_dmso_2h_p65_tag_count']])
    
    