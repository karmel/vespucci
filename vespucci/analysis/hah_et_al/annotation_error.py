'''
Created on Jun 9, 2013

@author: karmel

We want to compare Vespucci generated transcripts to those
derived from Hah et al's HMM (groHMM). See full notes in __init__.py for 
more information.

Methods here take genomic coordinates and calculate two kinds of error
versus reference data: number of reference transcripts broken up, and number
run together.
'''
from __future__ import division

class TranscriptEvaluator(object):
    colnames = ('chr','start','end','strand')
    reference = None
    target = None

    def set_reference(self, data):
        '''
        Data to be used as reference annotations.
        Data should be a DataFrame with chr, start, end, strand.
        '''
        self.reference = self.set_data(data)
        
    def set_target(self, data):
        '''
        Data to be evaluated.
        Data should be a DataFrame with chr, start, end, strand.
        '''
        self.target = self.set_data(data)
        
    def set_data(self, data):
        '''
        Validates passed data, sorts, and groups.
        Data should be a DataFrame with chr, start, end, strand.
        '''        
        ref = data[range(len(self.colnames))]
        ref.columns = self.colnames
        # Chr in first col?
        if ref['chr'][0][:3] != 'chr':
            raise Exception('First column is missing chromosome data.')
        # Convert strand to int.
        if ref['strand'][0] in ('+','-'):
            ref['strand'] = map(int, ref['strand'] == '-')
        
        ref = ref.sort(['chr','start','end','strand'])
        
        # Separated by chr, strand 
        return ref.groupby(['chr','strand'])
    
    def get_summed_error(self):
        '''
        Return the sum of 
        
        # the fraction of reference transcripts broken up, and
        # the fraction of target transcripts that run together references.
        
        '''
        
        broken_frac = self.count_broken_reference()#/self.reference.size().sum()
        run_frac = self.count_run_together_reference()#/self.target.size().sum()
        return broken_frac + run_frac
    
    def count_broken_reference(self):
        '''
        The first of the two criteria: how many reference transcripts are
        broken by target transcripts?
        '''
        return self.count_broken(self.reference, self.target)

    def count_run_together_reference(self):
        '''
        The second of the two criteria: how many reference transcripts are
        run together by target transcripts?
        
        Notably, this is the same as asking how many target transcripts
        are broken by reference transcripts.
        '''
        return self.count_broken(self.target, self.reference)
        
    def count_broken(self, broken, breaking):
        '''
        Get raw count of how many 'broken' transcripts are broken up
        by 'breaking' transcripts. As per Hah et al, we count 1 for each broken
        that has at least one breaking transcript end within it while another 
        breaking transcript begins within it. 
        For example, this configuration would get one count:
        
            [--------------------------------] Broken
        [-----------] [---------] [--------]   Breaking
        
        Note that this is a naive loop, and not efficient.
        Will suffice for now.
        '''
        count = 0
        for (chr, strand), group in broken:
            # Retrieve relevant targets
            try: breakers = breaking.get_group((chr, strand))
            except KeyError: continue # No target transcripts to count 
            
            for _, ref in group.iterrows():
                # Get first transcript end after reference transcript start
                end_past_start = breakers[breakers['end'] >= ref['start']][:1]
                # Get last transcript start before reference transcript end
                start_before_end = breakers[breakers['start'] <= ref['end']][-1:]
                
                # If they don't exist, we're safe; pass to next loop.
                if end_past_start.empty or start_before_end.empty: continue
                
                # If first start and last end are same transcript, we're safe.
                #     [----------------------]
                #  [--------------------]
                if end_past_start.index[0] == start_before_end.index[0]:
                    continue
                 
                # If both are contained within the reference, count a penalty:
                #     [----------------------]
                # [-------------] [-------------]
                
                if end_past_start['end'].values[0] <= ref['end'] \
                    and start_before_end['start'].values[0] >= ref['start']:
                        count += 1
                
        return count
    