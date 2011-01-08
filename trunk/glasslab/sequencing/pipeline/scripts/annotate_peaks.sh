#!/bin/bash

if [ "$CURRENT_PATH" == "" ]; then
	export CURRENT_PATH="/Users/karmel/Desktop/Projects/GlassLab/Repositories/glasslab/trunk"
fi 

export PYTHONPATH=$CURRENT_PATH:$PYTHONPATH

export PATH=/Volumes/Unknowme/bowtie/bowtie-0.12.5:$PATH
export BOWTIE_INDEXES=/Volumes/Unknowme/bowtie/bowtie-0.12.5/indexes

export DJANGO_SETTINGS_MODULE=glasslab.config.django_settings

python $CURRENT_PATH/glasslab/sequencing/pipeline/annotate_peaks.py $@
