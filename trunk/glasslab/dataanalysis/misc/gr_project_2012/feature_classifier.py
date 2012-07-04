'''
Created on Jul 4, 2012

@author: karmel

The goal here is to see if we can tease out which features are 
predictive of characteristics of interest, such as pausing ratio
or transrepression. Worth a stab.
'''
from glasslab.dataanalysis.misc.gr_project_2012.width_buckets import get_data_with_bucket_score
from glasslab.dataanalysis.machinelearning.logistic_classifier import LogisticClassifier


if __name__ == '__main__':
    learner = LogisticClassifier()
    dirpath = 'karmel/Desktop/Projects/Classes/Rotations/Finland 2012/GR Project/classification'
    dirpath = learner.get_path(dirpath)
    
    data = get_data_with_bucket_score(learner, dirpath)
    # Get mean of all values to compress
    grouped = data.groupby('glass_transcript_id',as_index=False).mean()
    # Except for tag_count which should be summed.
    grouped['tag_count'] = data['tag_count'].groupby('glass_transcript_id',as_index=False).sum()
    
    if True:
        # Can we predict pausing ratio?
        
        subdir = 'pausing_ratio_diff'
        # First do some column cleanup.
        dataset = grouped.filter(regex=r'(?!^(kla_dex_\d_bucket_score|kla_dex_bucket_score))')
        print dataset.columns
        print dataset.ix[0]
        print dataset.ix[100]
        print len(dataset)
        
        