'''
Created on Sep 24, 2010

@author: karmel

Functions and classes for parsing array-like delimited files.
'''
import numpy
import random

class DelimitedFileParser(object):
    file_name = None
    file = None
    header = False
    fields = None
    
    def __init__(self, file_name='', header=False):
        super(DelimitedFileParser,self).__init__()
        self.file_name = file_name
        self.file = open(file_name)
        self.header = header
        
    def convert_line_endings(self):
        output = self.file.read().replace('\r\n','\n').replace('\r','\n')
        outfile = open(self.file_name, 'w')
        outfile.write(output)
        outfile.close()
        self.file = open(self.file_name)
        
    def get_array(self, delimiter='\t', strip=False, cast_data_types=True):
        '''
        For initialized file, parse into numpy array and return.
        
        Omits empty lines and lines beginning with #
        '''
        # Strip quotation marks and whitespace
        if strip: clean = lambda x: x.strip('"').strip() 
        else: clean = lambda x: x
        
        # Try to cast as a float if desired
        if cast_data_types: cast = lambda x: self.cast_data_type(x)
        else: cast = lambda x: x
        
        # Create a list of tuples that will become the array
        data, data_types = [], []
        k = 0
        for line in self.file:
            if self.header and k == 0: 
                self.fields = line.strip('\n').split(delimiter)
            elif line.strip('\n') and line[:1] != '#':
                row = []
                for i,field in enumerate(line.strip('\n').split(delimiter)):
                    field = cast(clean(field)) or None
                    # Does the current data type match the expected?
                    # If not, default to str, or cast empty value
                    try:
                        if not isinstance(field, data_types[i][0]):
                            if field: 
                                data_types[i][0] = str # Most general field type
                                field = str(field)
                            else: field = data_types[i][0]()
                        data_types[i][1] = max(data_types[i][1], len(str(field)))
                    except IndexError: 
                        # Get data type and data size, or keep as None if this is an empty field
                        data_types.append(field and [field.__class__,len(str(field))] or [None,0])
                    except TypeError:
                        data_types[i] = field and [field.__class__,len(str(field))] or [None,0]
                    row.append(field)
                data.append(tuple(row))
            k += 1
            
        # If there is a header row, set the fields, and use it for column names in the array
        if self.header: 
            # Get rid of leftover "None"s (replace with 0-length strings), and set string length for string fields
            data_types = [(type == str and '|S%d' % length) or type or '|S1' for type, length in data_types]
            # Make sure every field has a name for column headings in the array
            field_names = [field or str(i) for i,field in enumerate(self.fields)]
            data_types = zip(field_names, data_types)
            
        arr = numpy.array(data, dtype=data_types)
        return arr
    
    def cast_data_type(self, x):
        '''
        Given field value x, guess whether data type is a float or string.
        '''
        try: return float(x)
        except ValueError: return str(x) 
