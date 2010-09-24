'''
Created on Jul 27, 2010

@author: karmel

Contains methods for importing and parsing csv files of microarray data.

Microarray data assumed to be a CSV file in the following format::
                                                                                                        sample_code_1, sample_code_2, sample_code_3
    FeatureNum, Row, Col, ProbeUID, ProbeName, GeneName, SystematicName, Description, Acc, Description  sample_type_1, sample_type_2, sample_type_2
    4937        59   7    4465  A_51_P518959  1110025P21    1110025P21    Unknown 1110025P21    Unknown    2539.06        2548.11        2057.45

'''
import csv
import numpy
from glasslab.utils.datatypes.basic_array import Sample, Gene

class MicroarrayImporter(object):
    reader = None
    file_name = None
    delimiter = ','
    
    # Importer will return the matrix of data, list of genes (rows), and list of samples (cols)
    matrix = None
    genes = None
    sample = None 
    
    gene_descriptors = None # List of gene descriptor fields contained with each row of data
    data_col_count = 0 # Number of rows dedicated to expression counts, rather than descriptive gene data
    descriptive_col_count = 0 # Number of rows dedicated to descriptive gene information, rather than expression counts
    data_points = None # List of lists to store CSV data before casting as a numpy array
    
    def __init__(self, file_name, delimiter=None):
        self.file_name = file_name
        if delimiter: self.delimiter = delimiter
        self.genes, self.samples = [], []
        self.data_points, self.gene_descriptors = [], []
        super(MicroarrayImporter, self).__init__()
        
    def get_data(self):
        self.parse_delimited_file()
        return self.matrix, self.genes, self.samples
    
    def parse_delimited_file(self):
        self.reader = csv.reader(open(self.file_name, 'rU'), delimiter=self.delimiter)
        
        for i, row in enumerate(self.reader):
            if i == 0: 
                self.add_samples(row)
            elif i == 1: 
                self.get_gene_descriptors(row)
                self.describe_samples(row)
            else:
                self.add_gene(row)
                self.add_row(row)
        self.matrix = self.data_points_to_matrix() 
                
    def add_samples(self, row):
        ''' 
        Given a parsed row with empty fields and sample codes,
        create and store a list of sample codes. 
        
        Also sets the count of rows that account for sample data as 
        opposed to descriptive gene data. 
        '''
        for field in row:
            if field:
                self.samples.append(Sample(code=field))
                self.data_col_count += 1
            else: self.descriptive_col_count += 1
                
    def describe_samples(self, row):
        ''' 
        Given a parsed row with gene description field names
        and sample types/descriptors, add the type information to the Sample 
        objects. 
        '''
        for i, field in enumerate(row[-(self.data_col_count):]):
            self.samples[i].type = field
                
    def get_gene_descriptors(self, row):
        ''' 
        Get the set of keys for the gene features that will be 
        specified with each row. 
        '''
        self.gene_descriptors = row[:self.descriptive_col_count]
         
    def add_gene(self, row):
        ''' 
        From each row, set up the field_name:value dictionary of gene descriptors,
        and add a new gene to the set. 
        '''
        descriptor_dict = dict(zip(self.gene_descriptors, row[:self.descriptive_col_count]))
        self.genes.append(Gene(**descriptor_dict))
        
    def add_row(self, row):
        ''' 
        From each row, add the actual expression count information. 
        '''
        self.data_points.append([float(val) for val in row[-(self.data_col_count):]])
        
    def data_points_to_matrix(self):
        ''' 
        Convert list of lists of expression data to numpy array for manipulation. 
        '''
        return numpy.array(self.data_points)

        
        