'''
Created on Mar 22, 2012

@author: karmel
'''
from glasslab.dataanalysis.base.datatypes import TranscriptAnalyzer
import os
import subprocess
import math

class MotifAnalyzer(TranscriptAnalyzer):
    '''
    For use with the HOMER motif finding program for analysis
    of enriched motifs in transcript sets.
    '''
    homer_bin = '/Applications/bioinformatics/homer/bin/'
    default_length = [8,10,12] # For use with findMotifsGenome.pl
    default_size = 200
    
    
    def run_homer(self, data, project_name, dirpath,
                  center=True, reverse=False, preceding=True, 
                  size=None, length=None, number_of_motifs=10,
                  bg='', genome='mm9', cpus=1):
        '''
        Run HOMER on passed set of transcripts, assuming a transcription_start,
        transcription_end, and chr_name.
        '''
        fullpath, homer_filename = self.prep_files_for_homer(data, 
                            project_name, dirpath, center, reverse, preceding, size)
        
        self.run_homer_with_pos_file(homer_filename, fullpath, center, size, 
                                     length, number_of_motifs, bg, genome, cpus)
        
    
    def prep_files_for_homer(self, data, project_name, dirpath,
                  center=True, reverse=False, preceding=True, size=None):
        '''
        Create tab-delimited files with Windows carriage returns for Homer.
        '''
        fullpath = self.get_filename(dirpath,project_name)
        self.make_directory(fullpath)
        
        # Create HOMER-compatible file.
        region_filename = self.get_filename(fullpath, project_name + '_regions.txt')
        homer_filename = self.get_filename(fullpath, project_name + '_regions_for_homer.txt')
        
        if not size: size = self.default_size
        if not center:
            first_strand, second_strand = 0, 1
            if reverse:
                # Take the end of the transcript, rather than the beginning. 
                first_strand, second_strand = 1, 0
            if preceding:
                # First, expand the whole transcript on either side
                data['transcription_start'] = data['transcription_start'] - size
                data['transcription_end'] = data['transcription_end'] + size
                # Then grab strand-dependent beginning and end
                data['transcription_end_alt'] = data[data['strand'] == first_strand]['transcription_start'] + size 
                data['transcription_start_alt'] = data[data['strand'] == second_strand]['transcription_end'] - size 
            else:
                data['transcription_end_alt'] = data[data['strand'] == first_strand]['transcription_start'] + size 
                data['transcription_start_alt'] = data[data['strand'] == second_strand]['transcription_end'] - size
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
        
        return fullpath, homer_filename
        
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
        
        fullpath = self.get_filename(dirpath,'homer_motifs_size_%s_len_%s' % (
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
    

    
    
if __name__ == '__main__':
    yzer = MotifAnalyzer()
    
    base_dirpath = yzer.get_path('karmel/GlassLab/Notes_and_Reports/NOD_BALBc/ThioMacs/Analysis_2012_06/')
    dirpath = yzer.get_filename(base_dirpath,'motifs/')
    filename = yzer.get_filename(os.path.dirname(base_dirpath), 'balbc_nod_vectors.txt')
    data = yzer.import_file(filename)
    
    bg = yzer.get_filename(dirpath, 'promoter_overlap/promoter_overlap_regions_for_homer.txt')
    
    data = data[data['transcript_score'] >= 10]
    data = data[data['has_refseq'] != 0]
    #data = data[data['has_refseq'] == 0]
    #data = data[data['distal'] == 't']
    #data = data[data['h3k4me2_notx_score'] > 0]
    #data = data[data['length'] > 200]
    #data = data[abs(data['balb_plating_notx_fc']) < 1]
    data = data[data['balb_nod_notx_1h_fc'] <= -1]
    
    #data = yzer.collapse_strands(data)
    
    yzer.run_homer(data, 'promoter_overlap_notx_1h_nod_down', dirpath, 
                   cpus=2, center=False, reverse=False, preceding=True, size=400, length=[8,10,12,15], bg=bg)