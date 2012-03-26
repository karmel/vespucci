'''
Created on Mar 22, 2012

@author: karmel
'''
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer
import os
import subprocess
import math
from pandas.core.frame import DataFrame

class MotifAnalyzer(TranscriptAnalyzer):
    '''
    For use with the HOMER motif finding program for analysis
    of enriched motifs in transcript sets.
    '''
    homer_bin = '/Applications/bioinformatics/homer/bin/'
    default_length = [8,10,12] # For use with findMotifsGenome.pl
    default_size = 200
    
    
    def run_homer(self, data, project_name, dirpath,
                  center=True, size=None, length=None, number_of_motifs=10,
                  bg='', genome='mm9', cpus=1):
        '''
        Run HOMER on passed set of transcripts, assuming a transcription_start,
        transcription_end, and chr_name.
        '''
        fullpath = os.path.join(dirpath,project_name)
        self.make_directory(fullpath)
        
        # Create HOMER-compatible file.
        region_filename = os.path.join(fullpath, project_name + '_regions.txt')
        homer_filename = os.path.join(fullpath, project_name + '_regions_for_homer.txt')
        
        if not size: size = self.default_size
        if not center:
            data['transcription_end_alt'] = data[data['strand'] == 0]['transcription_start'] + size 
            data['transcription_start_alt'] = data[data['strand'] == 1]['transcription_end'] - size
            data['transcription_start'] = data['transcription_start_alt'].fillna(data['transcription_start']).apply(int)
            data['transcription_end'] = data['transcription_end_alt'].fillna(data['transcription_end']).apply(int)
            
        data.to_csv(region_filename, 
                    cols=['id','chr_name','transcription_start','transcription_end','strand'],
                    header=False, index=False, sep='\t')
        # Convert to Windows line endings
        subprocess.check_call("sed ':a;N;$!ba;s/\n/\r/g' %s > %s" % (
                                                    self.sanitize_filename(region_filename),
                                                    self.sanitize_filename(homer_filename)),
                                                    shell=True)
        
        self.run_homer_with_pos_file(homer_filename, fullpath, center, size, 
                                     length, number_of_motifs, bg, genome, cpus)
        
        
    def run_homer_with_pos_file(self, homer_filename, dirpath,
                                center=True, size=None, length=None, number_of_motifs=10,
                                bg='', genome='mm9', cpus=1):
        
        
        if not size: size = self.default_size
        if center: size = '-%d,+%d' % (int(math.floor(.5*size)), int(math.ceil(.5*size)))
        else: size = str(size)
        
        if not length: length = self.default_length
        length = ','.join(map(str,length))
        
        if bg: bg = '-bg %s' % bg
        else: bg = ''
        
        fullpath = os.path.join(dirpath,'homer_motifs_size_%s_len_%s' % (
                                        size.replace(',','_'), length.replace(',','-'))
                                )
        self.make_directory(fullpath)
        
        command = '%sfindMotifsGenome.pl %s %s %s -size %s -len %s -p %d -S %d %s' % (
                                        self.homer_bin, self.sanitize_filename(homer_filename), 
                                        genome, self.sanitize_filename(fullpath), 
                                        size, length, cpus, number_of_motifs, bg)
        
        subprocess.check_call(command, shell=True)
        
        print 'Successfully executed command %s' % command
        
    def make_directory(self, fullpath):
        if os.path.exists(fullpath): 
            raise Exception('Directory %s already exists!' % fullpath)
            #print 'Directory %s already exists!' % fullpath 
        else:
            os.mkdir(fullpath)
            
    def sanitize_filename(self, filename):
        return filename.replace(' ','\ ')
    
    def collapse_strands(self, data):
        '''
        If the data is strand specific, we may want to collapse
        overlapping sense and antisense transcripts for motif finding.
        
        This is relevant in the case of eRNA, where transcription is 
        bidirectional, and we want the center of transcription.
        
        Testing:
        data = DataFrame({'chr_name': ['chr1', 'chr1', 'chr1','chr2','chr2',], 
                       'transcription_start': [0, 10, 21, 0, 5],
                       'transcription_end': [10, 20, 30, 10, 7], 
                       'strand': [0, 1, 0, 1, 0]},
                     )
        should yield
              chr_name strand transcription_end transcription_start
                0     chr1      0                20                   0
                2     chr1      0                30                  21
                3     chr2      1                10                   0

        '''
        compressed = []
        ordered = data.sort_index(by=['chr_name','transcription_start'])
        last = None
        for _, trans in ordered.iterrows():
            try:
                if trans['chr_name'] <= last['chr_name']\
                    and trans['transcription_start'] <= last['transcription_end']:
                        last['transcription_end'] = max(trans['transcription_end'],last['transcription_end'])
                else: 
                    compressed.append((last.name, last))
                    last = trans
            except TypeError: last = trans
        compressed.append((last.name, last))
            
        return DataFrame(dict(compressed)).transpose()
    
    
if __name__ == '__main__':
    yzer = MotifAnalyzer()
    
    dirpath = '/Users/karmel/GlassLab/Notes_and_Reports/NOD_BALBc/ThioMacs/Diabetic/Nonplated/Analysis/motifs/'
    filename = os.path.join(os.path.dirname(dirpath), 'balbc_nod_vectors.txt')
    data = yzer.import_file(filename)
    
    bg = os.path.join(dirpath, 'h3k4me2_all/h3k4me2_all_regions_for_homer.txt')
    
    #data = data[data['transcript_score'] >= 10]
    #data = data[data['has_refseq'] != 0]
    data = data[data['has_refseq'] == 0]
    data = data[data['h3k4me2_notx_score'] > 0]
    data = data[data['balb_plating_notx_fc'] < 1]
    data = data[data['balb_nod_notx_1h_fc'] < 1]
    data = data[data['nonplated_diabetic_balb_nod_notx_fc'] >= 1]
    
    data = yzer.collapse_strands(data)
    
    yzer.run_homer(data, 'nonplated_nod_up_h3k4me2', dirpath, cpus=5, bg=bg)#center=False, size=500)