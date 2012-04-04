'''
Created on Apr 2, 2012

@author: karmel

Used to get counts for enhancer types over triplicate motifs
for modeling rotation in Hoffmann lab.
'''
from __future__ import division
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer
import os


if __name__ == '__main__':
    yzer = TranscriptAnalyzer()
    
    dirpath = yzer.get_path('/karmel/Desktop/Projects/Classes/Rotations/Winter 2012/Endpoint analysis/')
    filename = os.path.join(dirpath, 'triplicate_motifs_k27_ctcf.txt')
    
    data = yzer.import_file(filename)
    data = data.fillna(0)
    
    data = data[data['refseq'] == 0]
    
    for pu_1 in ('__eq__','__gt__'):
        for cebpa in ('__eq__','__gt__'):
            for p65 in ('__eq__','__gt__'):
                for ctcf in ('__eq__','__gt__'):
                    for me2 in ('__eq__','__gt__'):
                        for k27 in ('__eq__','__gt__'):
                            for trans in ('__eq__','__gt__'):
                                    c = len(data[(getattr(data['pu_1'], pu_1)(0)) &
                                                   (getattr(data['cebpa'], cebpa)(0)) &
                                                   (getattr(data['p65'], p65)(0)) &
                                                   (getattr(data['ctcf'], ctcf)(0)) &
                                                   (getattr(data['me2'], me2)(0)) &
                                                   (getattr(data['k27'], k27)(0)) &
                                                   (getattr(data['trans'], trans)(0))])
                                    code = ''.join([x == '__gt__' and '2' or '0' for x in (pu_1, cebpa, p65, ctcf)])
                                    code2 = ''.join([x == '__gt__' and '1' or '0' for x in (me2, k27, trans)])
                                    print '\t'.join([code + code2, str(c), str(c/len(data))])
    
    print len(data)
    
