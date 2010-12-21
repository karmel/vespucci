'''
Created on Nov 15, 2010

@author: karmel
'''
from django.db import transaction, connections

def execute_query(query, using='default'):
    connection = connections[using]
    connection.close()
    cursor = connection.cursor()
    cursor.execute(query)
    transaction.commit_unless_managed()
    return cursor

def execute_query_without_transaction(query, using='default'):
    connection = connections[using]
    isolation_level = connection.isolation_level
    connection.close()
    connection.isolation_level = 0
    cursor = connection.cursor()
    cursor.execute(query)
    transaction.commit_unless_managed()
    connection.isolation_level = isolation_level
    return cursor

def fetch_rows(query, return_cursor=False, using='default'):
    connection = connections[using]
    connection.close()
    cursor = connection.cursor()
    cursor.execute(query)
    if return_cursor: return cursor.fetchall(), cursor
    return cursor.fetchall()
