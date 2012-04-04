'''
Created on Apr 3, 2012

@author: karmel


'''
from __future__ import division
import os
from glasslab.dataanalysis.graphing.seq_grapher import SeqGrapher


if __name__ == '__main__':
    yzer = SeqGrapher()
    
    dirpath = yzer.get_path('/karmel/Desktop/Projects/Classes/Rotations/Winter 2012/Endpoint analysis/for_minna/')
    filename = os.path.join(dirpath, 'merged_h3k4me2_notx.txt')
    
    data = yzer.import_file(filename)
    data['rpkm'] = 1000*data['trans']/data['width']
    
    data = data.fillna(0)
    
    data = data[data['refseq'] == 0]
    
    me2_tf = data[(data['pu_1'] + data['cebpa'] + data['p65'] > 0) & 
                    (data['ctcf'] == 0) &
                   (data['k27'] == 0) & (data['me2'] > 0) ]
    ctcf_tf = data[(data['pu_1'] + data['cebpa'] + data['p65'] > 0) & 
                    (data['ctcf'] > 0) &
                   (data['k27'] == 0) & (data['me2'] == 0) ]
    k27_tf = data[(data['pu_1'] + data['cebpa'] + data['p65'] > 0) & 
                    (data['ctcf'] == 0) &
                   (data['k27'] > 0) & (data['me2'] == 0) ]
    ctcf_me2_tf = data[(data['pu_1'] + data['cebpa'] + data['p65'] > 0) & 
                    (data['ctcf'] > 0) &
                   (data['k27'] == 0) & (data['me2'] == 0) ]
    k27_me2_tf = data[(data['pu_1'] + data['cebpa'] + data['p65'] > 0) & 
                    (data['ctcf'] == 0) &
                   (data['k27'] > 0) & (data['me2'] > 0) ]
    tf = data[(data['pu_1'] + data['cebpa'] + data['p65'] > 0) & 
                    (data['ctcf'] == 0) &
                   (data['k27'] == 0) & (data['me2'] == 0) ]

    me2_only = data[(data['pu_1'] == 0) & (data['cebpa'] == 0) &
                   (data['p65'] == 0) & (data['ctcf'] == 0) &
                   (data['k27'] == 0) & (data['me2'] > 0) ]
    ctcf_only = data[(data['pu_1'] == 0) & (data['cebpa'] == 0) &
                   (data['p65'] == 0) & (data['ctcf'] > 0) &
                   (data['k27'] == 0) & (data['me2'] == 0) ]
    k27_only = data[(data['pu_1'] == 0) & (data['cebpa'] == 0) &
                   (data['p65'] == 0) & (data['ctcf'] == 0) &
                   (data['k27'] > 0) & (data['me2'] == 0) ]
    ctcf_me2 = data[(data['pu_1'] == 0) & (data['cebpa'] == 0) &
                   (data['p65'] == 0) & (data['ctcf'] > 0) &
                   (data['k27'] == 0) & (data['me2'] == 0) ]
    k27_me2 = data[(data['pu_1'] == 0) & (data['cebpa'] == 0) &
                   (data['p65'] == 0) & (data['ctcf'] == 0) &
                   (data['k27'] > 0) & (data['me2'] > 0) ]
    nothing = data[(data['pu_1'] == 0) & (data['cebpa'] == 0) &
                   (data['p65'] == 0) & (data['ctcf'] == 0) &
                   (data['k27'] == 0) & (data['me2'] == 0) ]

    
    
    for group in (me2_only, ctcf_only, k27_only, ctcf_me2, k27_me2, nothing):
        print len(group), len(group)/len(data)
        
        
    if True:
        ax = yzer.boxplot([data['rpkm'], me2_tf['rpkm'], ctcf_tf['rpkm'],
                           k27_tf['rpkm'], ctcf_me2_tf['rpkm'], k27_me2_tf['rpkm'], tf['rpkm'],
                           me2_only['rpkm'], ctcf_only['rpkm'],
                           k27_only['rpkm'], ctcf_me2['rpkm'], k27_me2['rpkm'], nothing['rpkm']], 
                                  bar_names=['All Potential\nEnhancers', 
                                             'me2 + TF', 'CTCF + TF',  
                                             'K27 + TF', 
                                             'CTCF + me2\n+ TF', 'K27 + me2\n+ TF', 'TF',
                                             'me2 only', 'CTCF only',  
                                             'K27 only', 
                                             'CTCF + me2', 'K27 + me2',
                                             'No peaks',],
                                  title='GRO-seq RPKM at non-genic H3K4me2 regions', 
                                  xlabel='', ylabel='Tags per 1000bp in GRO-seq transcript overlapping H3K4me2 peak', 
                                  show_outliers=False, show_plot=False)
        
        yzer.save_plot(os.path.join(dirpath, 'groseq_rpkm_at_h3k4me2_peaks.png'))
        yzer.show_plot()
        
        
'''
-- With H3K27me3
select distinct on (e.id) e.*, e.id as me2, reg.id as refseq, p1.id as pu_1, p2.id as cebpa,
p3.id as p65, p5.id as k27, p6.id as ctcf, t.id as trans, t.tag_count 
from thiomac_chipseq_2011.peak_wt_notx_1h_h3k4me2_05_11 e

left outer join genome_reference_mm9.sequence_transcription_region reg
on e.chromosome_id = reg.chromosome_id
and e.start_end && reg.start_end 
left outer join thiomac_chipseq_2011.peak_wt_notx_1h_pu_1_05_11 p1
on e.chromosome_id = p1.chromosome_id
and e.start_end && p1.start_end
left outer join thiomac_chipseq_2011.peak_wt_notx_1h_cebpa_05_11 p2
on e.chromosome_id = p2.chromosome_id
and e.start_end && p2.start_end
left outer join thiomac_chipseq_2011.peak_wt_notx_1h_p65_10_11 p3
on e.chromosome_id = p3.chromosome_id
and e.start_end && p3.start_end
left outer join thiomac_chipseq_2009.peak_wt_notx_h3k27me3_02_09 p5
on e.chromosome_id = p5.chromosome_id
and e.start_end && p5.start_end
left outer join thiomac_chipseq_2009.peak_wt_notx_ctcf_02_09 p6
on e.chromosome_id = p6.chromosome_id
and e.start_end && p6.start_end
left outer join (select t.*, s.tag_count from glass_atlas_mm9_thiomac.glass_transcript t
join glass_atlas_mm9_thiomac.glass_transcript_source s
on t.id = s.glass_transcript_id
where s.sequencing_run_id = 219
) t
on e.chromosome_id = t.chromosome_id
and e.start_end && t.start_end



-- With H3K27me3
select distinct on (e.id) e.*, reg.id as refseq, p1.id as pu_1, p2.id as cebpa,
p3.id as p65, p4.id as me2, p5.id as k27, p6.id as ctcf, t.tag_count as trans, t.width
from thiomac_chipseq_2011.peak_merged_h3k4me2_05_11 e

left outer join genome_reference_mm9.sequence_transcription_region reg
on e.chromosome_id = reg.chromosome_id
and e.start_end && reg.start_end 
left outer join thiomac_chipseq_2011.peak_wt_notx_1h_pu_1_05_11 p1
on e.chromosome_id = p1.chromosome_id
and e.start_end && p1.start_end
left outer join thiomac_chipseq_2011.peak_wt_notx_1h_cebpa_05_11 p2
on e.chromosome_id = p2.chromosome_id
and e.start_end && p2.start_end
left outer join thiomac_chipseq_2011.peak_wt_notx_1h_p65_10_11 p3
on e.chromosome_id = p3.chromosome_id
and e.start_end && p3.start_end
left outer join thiomac_chipseq_2011.peak_wt_notx_1h_h3k4me2_05_11 p4
on e.chromosome_id = p4.chromosome_id
and e.start_end && p4.start_end
left outer join thiomac_chipseq_2009.peak_wt_notx_h3k27me3_02_09 p5
on e.chromosome_id = p5.chromosome_id
and e.start_end && p5.start_end
left outer join thiomac_chipseq_2009.peak_wt_notx_ctcf_02_09 p6
on e.chromosome_id = p6.chromosome_id
and e.start_end && p6.start_end
left outer join (select sum(s.tag_count) as tag_count, max(width(t.start_end)) as width, f.glass_peak_id 
from glass_atlas_mm9_thiomac.glass_transcript t
join glass_atlas_mm9_thiomac.glass_transcript_source s
on t.id = s.glass_transcript_id
join glass_atlas_mm9_thiomac.peak_feature f
on t.id = f.glass_transcript_id
where s.sequencing_run_id = 219
and f.sequencing_run_id = 510
and f.touches = True
group by f.glass_peak_id
) t
on e.id = t.glass_peak_id
'''