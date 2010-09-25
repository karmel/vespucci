'''
Created on Jul 27, 2010

@author: karmel
'''

class Gene(object):
    ''' 
    Convenience object for representing gene data. 
    
    Default attributes::
    
        probe_id, probe_name, probe_sequence, gene_name, 
        systematic_name, description, accessions_number, description_alt
    
    Any extra features passed into ``__init__`` will be automatically 
    added to the ``extra`` dict attribute.
    '''
    probe_id = None
    probe_name = None
    probe_sequence = None
    gene_name = None
    systematic_name = None
    description = None
    accession_number = None
    description_alt = None
    type = None
    
    protein_name = None
    location = None
    
    functions = None
    ''' GeneOntology DB terms for molecular functioning. '''
    processes = None
    ''' GeneOntology DB terms for biological processes. '''
    function_tree = None
    ''' 
    List of tuples, (distance to root node) from
    GeneOntology DB terms for molecular functioning. 
    '''
    process_tree = None
    ''' 
    List of tuples, (distance to root node) from
    GeneOntology DB terms for biological processes. 
    '''
    
    extra = None
    
    related_names = {'probe_uid': 'probe_id',
                     'accession': 'accession_number',
                     'definition': 'description',
                     'symbol': 'gene_name',
                     }
    
    def __init__(self, **kwargs):
        self.extra = {}
        for key, value in kwargs.items():
            # Normalize key names
            key = key.lower()
            if key in self.related_names: key = self.related_names[key]
            # Set attribute, or just save to extra list of attributes
            if hasattr(self, key): setattr(self, key, value)
            else: self.extra[key] = value
        super(Gene, self).__init__()
    
    def __repr__(self): return 'Gene record: %s' % self.gene_name
    
class Sample(object):
    ''' 
    Convenience object for representing a single sample across all surveyed genes. 
    
    Default attributes::
    
        code (i.e., r_49_4) and type (i.e., NOTX)
    
    Any extra features passed into ``__init__`` will be automatically 
    added to the ``extra`` dict attribute.
    '''
    code = None
    type = None
    control = None
    
    extra = None
    def __init__(self, code=None, type=None, **kwargs):
        if code: self.code = code
        if type: self.type = type
        self.extra = {}
        for key, value in kwargs.items():
            if hasattr(self, key): setattr(self, key, value)
            else: self.extra[key] = value
        super(Sample, self).__init__()
    
    def __repr__(self): return 'Sample record: %s (%s)' % (self.code, self.type)
