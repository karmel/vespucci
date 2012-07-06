'''
Created on Jun 25, 2012

@author: karmel
'''
from glasslab.dataanalysis.motifs.motif_analyzer import MotifAnalyzer

if __name__ == '__main__':
    yzer = MotifAnalyzer()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/GR chip/'
    dirpath = yzer.get_path(dirpath)
    
    motif_dirpath = yzer.get_filename(dirpath, 'motifs_2012_07/')
    filename = yzer.get_filename(dirpath, 'transcript_vectors.txt')
    
    data = yzer.import_file(filename)
    data = data.fillna(0)
    
    distal = data[data['distal'] == 't']
    refseq = data[data['has_refseq'] == 1]


    if True:    
        yzer.prep_files_for_homer(distal, 'distal', motif_dirpath, 
                                  center=False, reverse=False, preceding=False, size=200)
        yzer.prep_files_for_homer(refseq, 'refseq_promoter', motif_dirpath, 
                                  center=False, reverse=False, preceding=True, size=200)
    