'''
Created on Oct 1, 2010

@author: karmel

For use from data pipelining scripts. Make sure genome and output_dir
are passed in, and the CurrentPeak table is already set up.
'''
from glasslab.sequencing.datatypes.gene_ontology import GoSeqEnrichedTerm
from glasslab.utils.geneannotation.gene_ontology import GOAccessor
from glasslab.config.django_settings import DATABASES
from glasslab.utils.datatypes.genome_reference import SequenceDetail,\
    SequenceIdentifier, SequenceTranscriptionRegion
import traceback
import subprocess
import os 
from glasslab.sequencing.datatypes.tag import GlassTagSequence, GlassTag,\
    set_all_tag_table_names
from glasslab.config import current_settings

def get_goseq_annotation(genome, output_dir, file_name):
    '''
    Our peaks have all been saved and annotated; get enriched GO terms from GOSeq.
    
    To run::
    
        r /Path/to/R/script.r db_host db_port db_name db_user db_pass 
                sequence_detail_table seq_table sequence_transcription_region_table tag_seq_table 
                genome output_dir file_name
    
    Creates and saves plot of Probability Weighting Function, and
    creates a table that has GO term IDs and enrichment p-values.
    '''
    import glasslab.sequencing.geneontology.goseq as goseq
    r_script_path = os.path.join(os.path.dirname(goseq.__file__),'ontology_for_peaks.r')
    goseq_command = '%s "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (r_script_path,
                                                         DATABASES['default']['HOST'],
                                                         DATABASES['default']['PORT'],
                                                         DATABASES['default']['NAME'],
                                                         DATABASES['default']['USER'],
                                                         DATABASES['default']['PASSWORD'],
                                                         SequenceDetail._meta.db_table.replace('"','\\"'),
                                                         SequenceIdentifier._meta.db_table.replace('"','\\"'),
                                                         SequenceTranscriptionRegion._meta.db_table.replace('"','\\"'),
                                                         GlassTagSequence._meta.db_table.replace('"','\\"'),
                                                         genome, output_dir, file_name
                                                         )
    try: subprocess.check_call(goseq_command, shell=True)
    except Exception:
        raise Exception('Exception encountered while trying to get GOSeq analysis. Traceback:\n%s'
                                % traceback.format_exc())

def output_goseq_enriched_ontology(output_dir, file_name, table_name=None):
    '''
    For saved GoSeq term ids, output file of term id, term, and p val 
    for all terms with p val <= .05
    '''
    if table_name: GoSeqEnrichedTerm.set_table_name(table_name)
    else: GoSeqEnrichedTerm._meta.db_table = GlassTagSequence._meta.db_table + '_goseq'
    # Get list of (term id, p val) tuples
    enriched = GoSeqEnrichedTerm.objects.filter(p_value_overexpressed__lte=.05
                                    ).values_list('go_term_id','p_value_overexpressed')
    term_ids, p_vals = zip(*enriched)
    # Get corresponding terms for human readability
    term_names_by_id = dict(GOAccessor().get_terms_for_ids(list(term_ids)))
    term_rows = zip(term_ids, [term_names_by_id.get(id.strip(),'') for id in term_ids], p_vals)

    # Output tsv
    header = 'GO Term ID\tGO Term\tP-value of overexpression\n'
    output_tsv = header + '\n'.join(['\t'.join(map(lambda x: str(x).strip(), row)) for row in term_rows])
    file_path = os.path.join(output_dir,'%s_GOSeq_enriched_terms.tsv' % file_name)
    file = open(file_path, 'w')
    file.write(output_tsv)

if __name__ == '__main__':
    current_settings.CURRENT_SCHEMA = 'thiomac_groseq_nathan_2010_10'
    set_all_tag_table_names('ncor_ko_kla_1h')
    get_goseq_annotation('mm9', '/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/go_seq',
                         'ncor_ko_kla_1h')
    output_goseq_enriched_ontology('/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/go_seq',
                                   'ncor_ko_kla_1h')