'''
Created on Mar 22, 2012

@author: karmel
'''
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer
import os
import subprocess

class MotifAnalyzer(TranscriptAnalyzer):
    '''
    For use with the HOMER motif finding program for analysis
    of enriched motifs in transcript sets.
    '''
    
    def run_homer(self, data, project_name, dirpath):
        '''
        Run HOMER on passed set of transcripts, assuming a transcription_start,
        transcription_end, and chr_name.
        '''
        fullpath = os.path.join(dirpath,project_name)
        if os.path.exists(fullpath): 
            print 'Directory %s already exists!' % fullpath #raise Exception('Directory %s already exists!' % fullpath)
        else:
            os.mkdir(fullpath)
        
        # Create HOMER-compatible file.
        region_filename = os.path.join(fullpath, project_name + '_regions_for_homer.txt')
        data.to_csv(region_filename, 
                    cols=['id','chr_name','transcription_start','transcription_end','strand'],
                    header=False, index=False, sep='\t')
        # Convert to windows line endings
        subprocess.check_call("sed ':a;N;$!ba;s/\n/\r/g' %s" % region_filename, shell=True)
        
        
if __name__ == '__main__':
    yzer = MotifAnalyzer()
    
    dirpath = '/Users/karmel/GlassLab/Notes and Reports/NOD_BALBc/ThioMacs/Diabetic/Nonplated/Analysis/'
    filename = os.path.join(dirpath, 'balbc_nod_vectors.txt')
    data = yzer.import_file(filename)
    
    yzer.run_homer(data, 'h3k4me2_nonplated_up', dirpath)