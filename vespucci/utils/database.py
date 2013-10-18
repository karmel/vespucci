'''
Created on Nov 15, 2010

@author: karmel
'''
from django.db import transaction, connections
from vespucci.config import current_settings


def execute_query(query, 
                  using='default', 
                  return_cursor=False, 
                  discard_temp=False):
    connection = connections[using]
    connection.close()
    cursor = connection.cursor()
    cursor.execute(query)
    transaction.commit_unless_managed()
    if return_cursor: return cursor
    if discard_temp: discard_temp_tables(using=using)
    connection.close()

def execute_query_without_transaction(query, 
                                      using='default', 
                                      return_cursor=False):
    connection = connections[using]
    isolation_level = connection.isolation_level
    connection.close()
    connection.isolation_level = 0
    cursor = connection.cursor()
    cursor.execute(query)
    transaction.commit_unless_managed()
    connection.isolation_level = isolation_level
    if return_cursor: return cursor
    connection.close()

def fetch_rows(query, return_cursor=False, using='default'):
    connection = connections[using]
    connection.close()
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    if return_cursor: return result, cursor
    connection.close()
    return result

def discard_temp_tables(using='default'):
    '''
    Drops all temporary tables created in the current session.
    '''
    execute_query_without_transaction('DISCARD TEMP;', using=using)
    
def set_savepoint(name, using='default'):
    execute_query('SAVEPOINT {};'.format(name), using)
    print 'Setting ' + name
    current_settings.LAST_SAVEPOINT = name
def release_savepoint(name, using='default'):
    execute_query('RELEASE SAVEPOINT {};'.format(name), using)
    print 'Releasing ' + name
    if current_settings.LAST_SAVEPOINT == name: 
        current_settings.LAST_SAVEPOINT = None
def rollback_savepoint(name, using='default'):
    execute_query('ROLLBACK TO SAVEPOINT {};'.format(name), using)
    print 'Rolling back to ' + name
    if current_settings.LAST_SAVEPOINT == name: 
        current_settings.LAST_SAVEPOINT = None
    
class SqlGenerator(object):
    ''' 
    Parent class for schema-specific SQL generators.
    '''
    user = None
    def __init__(self, user=None):
        self.user = user or current_settings.DATABASES['default']['USER']
    
    def pkey_sequence_sql(self, schema_name, table_name):
        return """
        GRANT ALL ON TABLE "{0}"."{1}" TO  "{user}";
        CREATE SEQUENCE "{0}"."{1}_id_seq"
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        ALTER SEQUENCE "{0}"."{1}_id_seq" OWNED BY "{0}"."{1}".id;
        ALTER TABLE "{0}"."{1}" ALTER COLUMN id 
            SET DEFAULT nextval('"{0}"."{1}_id_seq"'::regclass);
        ALTER TABLE ONLY "{0}"."{1}" ADD CONSTRAINT {1}_pkey PRIMARY KEY (id);
        """.format(schema_name, table_name, user=self.user)

