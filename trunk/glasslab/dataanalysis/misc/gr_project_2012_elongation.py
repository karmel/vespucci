'''
Created on Jun 26, 2012

@author: karmel
'''
from glasslab.dataanalysis.graphing.basepair_counter import BasepairCounter

def set_up_sequencing_run_ids():
    # Sequencing run ids
    dmso = [[153, 152, 191, 201],[506, 588],[241],[589]]
    kla = [[141, 146, 182, 210],[505, 586],[245],[582]]
    kla_dex = [[12, 11, 122, 190, 209],[499, 587],[244],[584]]
    
    all_dmso, all_kla, all_kla_dex = [],[],[]
    for l in dmso: all_dmso.extend(l)
    for l in kla: all_kla.extend(l)
    for l in kla_dex: all_kla_dex.extend(l)
    
    run_ids = {'dmso': [all_dmso] + dmso,
               'kla': [all_kla] + kla,
               'kla_dex': [all_kla_dex] + kla_dex,
               }
    return run_ids

def get_sequencing_run_id_sets():
    run_ids = set_up_sequencing_run_ids()
    all_dmso, all_kla, all_kla_dex = run_ids['dmso'][0],run_ids['kla'][0],run_ids['kla_dex'][0]
    dmso, kla, kla_dex = run_ids['dmso'][1:],run_ids['kla'][1:],run_ids['kla_dex'][1:]
    return dmso, kla, kla_dex, all_dmso, all_kla, all_kla_dex
    
def total_tags_per_run():
    # Return total tags for ease of scaling
    # All, then by group. 
    total_tags = {'dmso': [104515661, 25774703, 31352700, 24315409, 23072849],
                  'kla': [85732816, 20452108, 27779082, 22166147, 15335479],
                  'kla_dex': [86164565, 21986129, 25467231, 22138023, 16573182]
                  }
    return total_tags

if __name__ == '__main__':
    
    run_ids = set_up_sequencing_run_ids()
    total_tags = total_tags_per_run()
    
    # Decompose data into lists
    # We want basepairs -500 to 2000
    grapher = BasepairCounter()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/basepair_counts'
    dirpath = grapher.get_path(dirpath)
    
    if False:
        filename = grapher.get_filename(dirpath, 'all_transcripts_by_refseq.txt')
        data = grapher.import_file(filename)
    
        data_refseq = data[data['refseq_major'] == 't']
        data_non_refseq = data[data['refseq_major'] != 't']
        ax = grapher.plot_tags_per_basepair([data_refseq],
                                            labels=['RefSeq', 'Not RefSeq'],
                                            title='Tag localization for all runs, RefSeq')
        grapher.save_plot(grapher.get_filename(dirpath, 'all_transcripts_only_refseq.png'))
        grapher.show_plot()
    if False:
        filename = grapher.get_filename(dirpath, 'all_transcripts_by_sequencing_run_by_refseq.txt')
        data = grapher.import_file(filename)
    
        data = data[data['refseq_major'] == 't']
        
        groups = [data[data['sequencing_run_id'].isin(run_ids['dmso'][0])],
                  data[data['sequencing_run_id'].isin(run_ids['kla'][0])],
                  data[data['sequencing_run_id'].isin(run_ids['kla_dex'][0])]]
        
        # Combine for sequencing runs now
        for i, group in enumerate(groups):
            groups[i] = group.groupby(['basepair'], as_index=False).sum()
         
        totals = zip(*total_tags.values())[0]
        tag_scalars = grapher.get_tag_scalars(totals)
        ax = grapher.plot_tags_per_basepair(groups,
                                            labels=['DMSO', 'KLA', 'KLA+Dex'],
                                            title='Tag localization for RefSeq transcripts by run type',
                                            tag_scalars=tag_scalars)
        grapher.save_plot(grapher.get_filename(dirpath, 'refseq_by_run_type.png'))
        grapher.show_plot()
        
    if True:
        filename = grapher.get_filename(dirpath, 'refseq_by_state.txt')
        data = grapher.import_file(filename)
    
    
        states = (#('Special', 'group_{0}'),
                  #('KLA','kla_{0}state'), ('KLA+Dex','kla_dex_{0}state'),
                  ('KLA+Dex over KLA','dex_over_kla_{0}state'))
        for desc,state in states:
            for replicate_id in ('',1,2,3,4):
                rep_str = replicate_id and '{0}_'.format(replicate_id) or replicate_id
                state_str = state.format(rep_str)
                
                # Include all transcripts at once, but only do it once.
                if desc == 'Special': 
                    datasets = [('All RefSeq', data),
                                ('Up > 2x in KLA, Down > 1.5x from that in Dex', 
                                 data[(data['kla_{0}state'.format(rep_str)] == 1)
                                      & (data['dex_over_kla_{0}state'.format(rep_str)] == -1)]),]
                else:
                    datasets = [('No change in {0}'.format(desc), data[data[state_str] == 0]),
                                ('Up in {0}'.format(desc), data[data[state_str] == 1]),
                                ('Down in {0}'.format(desc), data[data[state_str] == -1]),]
                
                for label, dataset in datasets:
                    slug_label = label.lower().replace(' ','_')
                    data_grouped = dataset.groupby(['basepair','sequencing_run_id'], as_index=False).sum()
                    
                    groups = [data_grouped[data_grouped['sequencing_run_id'].isin(
                                                    run_ids['dmso'][replicate_id or 0])],
                              data_grouped[data_grouped['sequencing_run_id'].isin(
                                                    run_ids['kla'][replicate_id or 0])],
                              data_grouped[data_grouped['sequencing_run_id'].isin(
                                                    run_ids['kla_dex'][replicate_id or 0])]]
                    
                    # Combine for sequencing runs now
                    for i, group in enumerate(groups):
                        groups[i] = group.groupby(['basepair'], as_index=False).sum()
                        
                    totals = zip(*total_tags.values())[replicate_id or 0]
                    tag_scalars = grapher.get_tag_scalars(totals)
                    ax = grapher.plot_tags_per_basepair(groups,
                                labels=['DMSO', 'KLA', 'KLA+Dex'],
                                title='Tag localization for RefSeq: {0}, {1}'.format(label,
                                        replicate_id and 'Group {0}'.format(replicate_id) or 'overall'),
                                tag_scalars=tag_scalars)
                    grapher.save_plot(grapher.get_filename(dirpath, 
                                '{0}_refseq_by_run_type_{1}.png'.format(slug_label,
                                        replicate_id and 'group_{0}'.format(replicate_id) or 'all')))
                    #grapher.show_plot()
                    
            
        