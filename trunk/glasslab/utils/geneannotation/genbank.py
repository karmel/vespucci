'''
Created on Sep 1, 2010

@author: karmel
'''
from Bio import Entrez
import traceback
from glasslab.utils.datatypes.basic_array import Gene
from glasslab.utils.geneannotation.gene_ontology import GOAccessor

Entrez.email = 'karmelallison@ucsd.edu'

class GeneAnotator(object):
    def search_gene(self, q='', return_all=False):
        '''
        Look up passed search term in GenBank. Return first or all results.
        '''
        ids = self._search_db('gene', q)
        if not return_all: ids = ids[:1] 
        results = self.fetch_from_db('gene', ids)
        genes = self._genes_from_results(results)
        if not return_all: return genes[0]
        else: return genes
    
    def search_genes(self, qs=None, return_all=False):
        '''
        Look up passed search terms in GenBank. Return first or all results.
        '''
        id_list = []
        for q in qs:
            ids = self._search_db('gene', q)
            if return_all: id_list += ids
            else: id_list.append(ids[0])
        results = self.fetch_from_db('gene', id_list)
        return self._genes_from_results(results)
    
    def annotate_genes(self, genes, overwrite=False):
        '''
        Given a set of genes, annotate each with passed information.
        
        Returns annotated genes.
        '''
        id_list = []
        for gene in genes:
            ids = self._search_db('gene', gene.gene_name)
            id_list.append(ids[0])
        results = self.fetch_from_db('gene', id_list)
        return self._annotate_from_results(results, genes, overwrite=overwrite)
        
    def _search_db(self, db, q='', human=True):
        # Search for term
        try:
            handle = Entrez.esearch(db=db,term=q + (human and ' (Homo sapiens[Organism])' or ''))
            search_results = Entrez.read(handle)
        except Exception:
            raise SearchFailedError('Searching NCBI %s database failed with error:\n%s' 
                                        % (db, traceback.format_exc()))
        try:
            id_list = search_results['IdList']
        except Exception:
            raise SearchFailedError('Search results were unexpected:\n%s' % handle.read())
        
        if not id_list: return self._search_db(db, q, human=False)
        return id_list
    
    def fetch_from_db(self, db, id_list):
        '''
        Retrieve one or all genes looked up by ID.
        '''
        results = self._retrieve_records(db, id_list)
        
        # Error handling
        if len(results) != len(id_list):
            results = []
            # Try one-by-one
            for id in id_list:
                try: results.append(self._retrieve_records(db, [id])[0])
                except Exception: results.append(None)
        
        return results
    
    def _retrieve_records(self, db, id_list):
        try:
            handle = Entrez.efetch(db=db, id=','.join(id_list), retmode='xml')
            result = Entrez.read(handle)
        except Exception:
            raise SearchFailedError('Searching NCBI %s database failed with error:\n%s' 
                                    % (db, traceback.format_exc())) 
        try:
            return result
        except Exception:
            raise SearchFailedError('Search results were unexpected:\n%s' % handle.read())

    def _genes_from_results(self, results):
        converter = GenBankConverter()
        genes = []
        for result in results:
            if not result: genes.append(None) 
            else: genes.append(converter.gene_from_gene_xml(result))
        return genes
    
    def _annotate_from_results(self, results, genes, overwrite=False):
        converter = GenBankConverter()
        annotated = []
        for i, result in enumerate(results):
            if result: 
                gene = converter.gene_from_gene_xml(result, genes[i], overwrite=overwrite)
                annotated.append(gene)
        return genes        

class GenBankConverter(object):
    '''
    Converts returned XML and other data types into pythonic objects.
    '''
    def gene_from_gene_xml(self, dict, gene=None, overwrite=False):
        '''
        Convert dict of xml values returned by Gene DB lookup as Gene object.
        '''
        translated = {}
        translated['gene_name'] = self._get_val_from_keys(dict,'Entrezgene_gene','Gene-ref', 'Gene-ref_locus')
        translated['description'] = self._get_val_from_keys(dict,'Entrezgene_gene','Gene-ref', 'Gene-ref_desc')
        translated['lineage'] = self._get_val_from_keys(dict, 'Entrezgene_source', 'BioSource', 'BioSource_org', 'Org-ref', 
                                                        'Org-ref_orgname', 'OrgName', 'OrgName_lineage')
        translated['summary'] = self._get_val_from_keys(dict, 'Entrezgene_summary')
        translated['location'] = self._get_val_from_keys(dict, 'Entrezgene_location', 0, 'Maps', 'Maps_display-str')
        translated['protein_name'] = self._get_val_from_keys(dict, 'Entrezgene_prot', 'Prot-ref','Prot-ref_name', 0)
        
        translated['functions'], translated['processes'], \
            translated['function_tree'], translated['process_tree'] = self._get_ontological_annotation(dict)
        
        if not gene: return Gene(**translated)
        else:
            for key, val in translated.items():
                if hasattr(gene, key):
                    if not getattr(gene, key) or overwrite: 
                        setattr(gene, key, val)
                else:
                    if not gene.extra.get(key, None) or overwrite: 
                        gene.extra[key] = val
            return gene
    
    def _get_val_from_keys(self, dict, *args):
        base = dict
        try:
            for arg in args: base = base[arg]
        except KeyError: return None
        return base
    
    def _get_ontological_annotation(self, dict):
        comments = self._get_val_from_keys(dict,'Entrezgene_properties')
        functions, processes = [], []
        function_tree, process_tree = set(), set()
        go_accessor = GOAccessor()
        if comments:
            for comment in comments:
                try:
                    if comment.get('Gene-commentary_heading',None) == 'GeneOntology':
                        for section in comment['Gene-commentary_comment']:
                            self._data_for_ontology_type(section, functions, 
                                                         function_tree, go_accessor, 
                                                         'Function')                  
                            self._data_for_ontology_type(section, processes, 
                                                         process_tree, go_accessor, 
                                                         'Process')
                except KeyError: pass
        return functions, processes, list(function_tree), list(process_tree)
        
    def _data_for_ontology_type(self, section, all, tree, go_accessor, type='Function'):
        if section['Gene-commentary_label'] == type:
            for source in section['Gene-commentary_comment']:
                for detail in source['Gene-commentary_source']:
                    # Add name to full list
                    term = detail['Other-source_anchor']
                    all.append(term)
                    # Add genericized names to generic list
                    term_id = self._get_val_from_keys(detail, 'Other-source_src','Dbtag','Dbtag_tag','Object-id','Object-id_id')
                    if term_id:
                        try: 
                            terms = go_accessor.get_generic_ancestors(term_id)
                            if terms: tree |= set(terms)
                        except Exception: pass
        
class SearchFailedError(Exception): pass

if __name__ == '__main__':
    result = GeneAnotator().search_genes(['4930540L03Rik', '5730442P18Rik', '5930431H10', 'Abt1', 'Akap7','Zswim2'])
    print result