#!/bin/bash

export PYTHONPATH=$CURRENT_PATH:$PYTHONPATH

export DJANGO_SETTINGS_MODULE=vespucci.config.current_settings

python $CURRENT_PATH/vespucci/atlas/pipeline/transcripts_from_tags.py $@
