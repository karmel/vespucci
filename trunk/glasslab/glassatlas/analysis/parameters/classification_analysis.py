'''
Created on Feb 16, 2011

@author: karmel
'''
from glasslab.glassatlas.analysis.parameters.parameter_performance import ParameterPerformance
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'roc':
        ParameterPerformance.draw_roc()
    else:
        ParameterPerformance.analyze_all_transcripts()
        ParameterPerformance.draw_roc()