'''
Created on Oct 12, 2010

@author: karmel

One-off script for retrieving and saving intersections of data by GO Term.
'''
from glasslab.utils.geneannotation.gene_ontology import GOAccessor
from django.db import connection
import os

class IntersectionAnalyzer(object):
    go_term_ids = None
    output_dir = None
    gene_names = None
    tables = {
                #'ncor_ko_kla_1h': '"current_projects"."peaks_nathan_ncor_ko_kla_1h_2010-10-13_11-53-21"', 
                #'ncor_ko_kla_12h': '"current_projects"."peaks_nathan_ncor_ko_kla_12h_2010-10-13_11-34-53"', 
                'ncor_ko_notx_1h': '"current_projects"."peaks_nathan_ncor_ko_notx_1h_2010-10-13_11-43-22"',
                'ncor_ko_notx_12h': '"current_projects"."peaks_nathan_ncor_ko_notx_12h_2010-10-13_11-24-48"',
                #'wt_kla_1h': '"current_projects"."peaks_nathan_wt_kla_1h_2010-10-13_12-35-14"',
                #'wt_kla_12h': '"current_projects"."peaks_nathan_wt_kla_12h_2010-10-13_11-23-44"',
                'wt_notx_1h': '"current_projects"."peaks_nathan_wt_notx_1h_2010-10-13_12-10-26"',
                'wt_notx_12h': '"current_projects"."peaks_nathan_wt_notx_12h_2010-10-13_11-25-03"',
                
                #'ncor_ko_kla_1h_with_control': '"current_projects"."peaks_ncor_ko_kla_1h_with_control_2010-10-13_16-42-06"',
                #'ncor_ko_kla_12h_with_control': '"current_projects"."peaks_ncor_ko_kla_12h_with_control_2010-10-13_17-39-44"',
                #'wt_kla_1h_with_control': '"current_projects"."peaks_wt_kla_1h_with_control_2010-10-13_17-40-39"',
                #'wt_kla_12h_with_control': '"current_projects"."peaks_wt_kla_12h_with_control_2010-10-13_17-32-33"',
                #'ncor_ko_notx_1h_with_control': '"current_projects"."peaks_ncor_ko_notx_1h_with_control_2010-10-14_11-34-37"',
                #'ncor_ko_notx_12h_with_control': '"current_projects"."peaks_ncor_ko_notx_12h_with_control_2010-10-14_11-26-42"',
                #'wt_notx_1h_with_control': '"current_projects"."peaks_wt_notx_1h_with_control_2010-10-14_11-19-20"',
                #'wt_notx_12h_with_control': '"current_projects"."peaks_wt_notx_12h_with_control_2010-10-14_11-13-10"',
              }
    
    
    per_table_sql_select = """
        SELECT DISTINCT 
            (peaks.chromosome || '-' || peaks.id) as "unique_id", 
            peaks.chromosome,
            peaks."start",
            peaks."end", 
            (CASE WHEN tss.direction = 1 THEN '-'
                ELSE '+'
                END) as direction,
            peaks."length",
            peaks."summit",
            peaks."tag_count",
            peaks."log_ten_p_value",
            peaks."fold_enrichment",
            peaks."distance",
            (CASE WHEN loc.id IS NOT NULL THEN loc.description
                WHEN i_description.description IS NOT NULL THEN i_description.description
                ELSE 'Intergenic'
                END) as "chromosome_location_annotation",
            seq.sequence_identifier,
            detail.unigene_identifier, 
            detail.ensembl_identifier, 
            detail.gene_name, 
            detail.gene_alias, 
            detail.gene_description 
        FROM "genome_reference"."sequence_identifier" seq
        JOIN "genome_reference"."transcription_start_site" tss
            ON tss.sequence_identifier_id = seq.id
        JOIN "genome_reference"."gene_detail" detail
            ON detail.sequence_identifier_id = seq.id
        JOIN %s peaks
            ON peaks.transcription_start_site_id = tss.id
        LEFT OUTER JOIN "genome_reference"."chromosome_location_annotation_mm9" loc 
            ON peaks.chromosome_location_annotation_id = loc.id
        LEFT OUTER JOIN "genome_reference"."chromosome_location_annotation_mm9_intergenic" intergenic 
            ON peaks.chromosome_location_annotation_intergenic_id = intergenic.id
        LEFT OUTER JOIN "genome_reference"."intergenic_chromosome_location_description" i_description
            ON intergenic.description_id = i_description.id
        """
        
    per_set_sql_select = """
        SELECT DISTINCT 
            (tss.chromosome || '-' || tss.id) as "tss_unique_id", 
            tss.chromosome,
            tss."start",
            tss."end", 
            (CASE WHEN tss.direction = 1 THEN '-'
                ELSE '+'
                END) as direction,
            seq.sequence_identifier,
            detail.unigene_identifier, 
            detail.ensembl_identifier, 
            detail.gene_name, 
            detail.gene_alias, 
            detail.gene_description 
        FROM "genome_reference"."sequence_identifier" seq
        JOIN "genome_reference"."transcription_start_site" tss
            ON tss.sequence_identifier_id = seq.id
        JOIN "genome_reference"."gene_detail" detail
            ON detail.sequence_identifier_id = seq.id
        """
        
    where_sql = """ WHERE detail.gene_name IN (%s) """
        
    def __init__(self, go_term_ids=None, output_dir=''):
        if go_term_ids: self.go_term_ids = go_term_ids
        if output_dir: self.output_dir = output_dir
        
        go_accessor = GOAccessor()
        if self.go_term_ids:
            self.gene_names = go_accessor.get_gene_names_for_category(self.go_term_ids)
            self.where_sql = self.where_sql % ("'" + "','".join(self.gene_names) + "'")
        else: self.where_sql = ' WHERE 1=1 '
        
    def query_for_tables(self, keys=None):
        '''
        For passed set of keys or all keys, find peaks matching the selected 
        GO term ids and save to files.
        ''' 
        keys = keys or self.tables.keys()
        for key in keys:
            self.query_for_table(key)
            
    def query_for_table(self, key):
        '''
        Set up SQL, query database, and save to file for passed table.
        '''
        sql = self.per_table_sql_select % self.tables[key]
        sql += self.where_sql
        
        file_path = os.path.join(self.output_dir,'%s_per_table_gene_specific.tsv' % key)
        self._output_for_query(sql, file_path)
        
        
    def _output_for_query(self, sql, file_path):
        # Query table
        cursor = connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        
        # Save results to TSV file in self.output_dir
        output = '\t'.join([field[0] for field in cursor.description]) + '\n'
        output += '\n'.join(['\t'.join(map(lambda x: str(x),row)) for row in result])
        
        file = open(file_path, 'w')
        file.write(output)
        
    def query_differential_intersections(self, subsets=None):
        '''
        Get each table alone, then the particular subsets as passed.
        
        Subsets is a dict of category_name: [list of member table keys].
        '''
        #for key in self.tables:
        #    self._output_for_exclusive_subset([key], '%s_only' % key)
        
        if subsets:
            for name, subset in subsets.items(): 
                self._output_for_exclusive_subset(subset, '%s_shared_only' % name)
            
    def _output_for_exclusive_subset(self, include_keys, file_name=''):
        # Set up SQL statements
        include_sql = " JOIN %s %s ON %s.transcription_start_site_id = tss.id \n"
        exclude_sql = "LEFT OUTER " + include_sql
        exclude_where = " %s.transcription_start_site_id IS NULL \n"
        
        sql = self.per_set_sql_select
        where_sql = []
        for key in include_keys:
            sql += include_sql % (self.tables[key], key, key)
        for exclude_key in self.tables.keys():
            if exclude_key in include_keys: continue 
            sql += exclude_sql % (self.tables[exclude_key], exclude_key, exclude_key)
            where_sql.append(exclude_where % exclude_key)
        sql += self.where_sql + (where_sql and "AND " + " AND ".join(where_sql) or '')
        file_path = os.path.join(self.output_dir,'%s.tsv' % file_name)
        self._output_for_query(sql, file_path)
            
        
        
        
if __name__ == '__main__':
    """
    analyzer = IntersectionAnalyzer(go_term_ids=['GO:0046903'],
                                    output_dir='/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/secretion')
    
    analyzer = IntersectionAnalyzer(go_term_ids=['GO:0046394'],
                                    output_dir='/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/lipid_synthesis')
    """
    analyzer = IntersectionAnalyzer(go_term_ids=None,
                                    output_dir='/Users/karmel/Desktop/Projects/GlassLab/Data/Sequencing/GroSeq/Nathan_NCoR_KO_2010_10_08/all_notx')
    
    subsets={#'ncor_ko_kla_1h': ['ncor_ko_kla_1h','ncor_ko_kla_12h',],
             #'wt_kla_vs_ncor_ko_kla': ['wt_kla_1h','wt_kla_12h'],
             #'all_kla': ['ncor_ko_kla_1h','ncor_ko_kla_12h','wt_kla_1h','wt_kla_12h'],
             'ncor_ko_notx_vs_wt_notx': ['ncor_ko_notx_1h','ncor_ko_notx_12h'],
             'wt_notx_vs_ncor_ko_notx': ['wt_notx_1h','wt_notx_12h'],
             'all_notx': ['ncor_ko_notx_1h','ncor_ko_notx_12h','wt_notx_1h','wt_notx_12h'],
            #'wt': ['wt_kla_1h','wt_kla_12h','wt_notx_1h','wt_notx_12h'],
            #'ncor_ko_wt_notx': ['ncor_ko_kla_1h','ncor_ko_kla_12h','ncor_ko_notx_1h','ncor_ko_notx_12h','wt_notx_1h','wt_notx_12h'],
            #'ncor_ko_kla_with_control': ['ncor_ko_kla_1h_with_control','ncor_ko_kla_12h_with_control',],
            #'wt_notx_with_control': ['wt_notx_1h_with_control','wt_notx_12h_with_control',],
            #'ncor_ko_notx_with_control': ['ncor_ko_notx_1h_with_control','ncor_ko_notx_12h_with_control',],
             }
    analyzer.query_for_tables()
    analyzer.query_differential_intersections(subsets)
        