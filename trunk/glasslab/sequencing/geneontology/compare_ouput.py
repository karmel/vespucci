'''
Created on Oct 5, 2010

@author: karmel

With a set of output TSV files, separate into desired chunks.
'''
from glasslab.utils.parsing.delimited import DelimitedFileParser
import itertools
import os

class GOOutputAnalyzer(object):
    output_dir = '/Users/karmel/Desktop/Projects/GlassLab/SourceData/ThioMac_Lazar/analysis/GO_terms'
    types = {'PPARg': ['/Users/karmel/Desktop/Projects/GlassLab/SourceData/ThioMac_Lazar/output/SRR039818_macrophage_PPARg/macrophage_PPARg_GO_enriched_terms.tsv',
                       '/Users/karmel/Desktop/Projects/GlassLab/SourceData/ThioMac_Lazar/output/SRR039819_macrophage_PPARg/macrophage_PPARg_GO_enriched_terms.tsv'],
             'CEBpb': ['/Users/karmel/Desktop/Projects/GlassLab/SourceData/ThioMac_Lazar/output/SRR039822_macrophage_CEBPb/macrophage_CEBPb_GO_enriched_terms.tsv'],
             'PU.1': ['/Users/karmel/Desktop/Projects/GlassLab/SourceData/ThioMac_Lazar/output/SRR039821_macrophage_PU_1/macrophage_PU_1_GO_enriched_terms.tsv'],
             'H3K9Ace': ['/Users/karmel/Desktop/Projects/GlassLab/SourceData/ThioMac_Lazar/output/SRR039823_macrophage_H3K9Ace/macrophage_H3K9Ace_GO_enriched_terms.tsv'],
             }
    
    def generate_union_files(self):
        datasets = {}
        union_all = None
        combos = [list(itertools.combinations(self.types.keys(),x)) for x in xrange(1,len(self.types.keys()))]
        combos.reverse()
        combos = list(itertools.chain(*combos))
        union_combos = {}
        for key, files in self.types.items():
            unique_by_go_id = {}
            for path in files:
                data = DelimitedFileParser(path).get_array()[1:]
                # Add entry to dict: GO_ID: data row, overwriting shared GO_IDs
                unique_by_go_id.update(zip(data[:,0],data))
            datasets[key] = unique_by_go_id
            try: union_all &= set(unique_by_go_id.keys())
            except TypeError: union_all = set(unique_by_go_id.keys())
            for combo in combos:
                if key in combo:
                    try: union_combos[combo] &= set(unique_by_go_id.keys())
                    except KeyError: union_combos[combo] = set(unique_by_go_id.keys())
        
        # Prep for file writing
        header = 'GO Term ID\tGO Term\n'
            
        already_used = set([]) | (union_all)
        for combo in combos:
            union_combos[combo] -= already_used
            already_used |= union_combos[combo] 
            output = header + '\n'.join(['\t'.join(datasets[combo[0]][go_id]) for go_id in union_combos[combo]])
            file_name = 'unique_go_terms_' + '_'.join(combo) + '.tsv'
            f = open(os.path.join(self.output_dir,file_name),'w')
            f.write(output)
            
        # Finally, for union all:
        output = header + '\n'.join(['\t'.join(datasets['PPARg'][go_id][:2]) for go_id in union_all])
        file_name = 'unique_go_terms_union_all.tsv'
        f = open(os.path.join(self.output_dir,file_name),'w')
        f.write(output)
        
        
        
if __name__ == '__main__':
    GOOutputAnalyzer().generate_union_files()  