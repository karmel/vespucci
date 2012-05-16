'''
Created on Nov 15, 2010

@author: karmel
'''
from django.db import transaction, connections
from subprocess import check_call, check_output
from glasslab.config import current_settings
import subprocess
import datetime
from psycopg2 import OperationalError

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

def restart_server():
    '''
    On the Mac server, the Postgres server for some unknown reason
    does not release memory until restarted. We restart the server programmatically
    in certain circumstances to force the release of built of memory.
    
    To do this, we need to circumvent permissions issues by logging in 
    as user postgres. So, we ssh in with a public key set up on the 
    code-runner's machine (karmel@glass.bioinforma.tc, in this case)
    that is known to the postgres@glass.bioinforma.tc user. Then we restart 
    the server as the postgres user. 
    
    Notably, because we are restarting a daemon process, we have to 
    redirect all output into dev/null, or else the cursor doesn't return.
    
    We want to check first that the server knows it has restarted, and
    then that it can actually accept incoming queries.
    '''
    check_call('{0} "{1}/bin/pg_ctl restart -D {1}/data/ </dev/null >/dev/null 2>&1 &"'.format(
                                            current_settings.PG_ACCESS_CMD, 
                                            current_settings.PG_HOME), shell=True)
    
    # Make sure everything went as planned
    time_to_wait = 5*60
    server_is_starting = datetime.datetime.now()
    while server_is_starting:
        try:
            status = check_output('{0} "{1}/bin/pg_ctl status -D {1}/data/"'.format(
                                            current_settings.PG_ACCESS_CMD, 
                                            current_settings.PG_HOME), shell=True)
            server_is_starting = False
        except subprocess.CalledProcessError:
            if (datetime.datetime.now() - server_is_starting).seconds > time_to_wait:
                server_is_starting = False
                raise Exception('Could not restart server after {0} seconds. Please investigate.'.format(time_to_wait))
    
    if status.find('server is running') < 0: 
        raise Exception('Could not restart server! Status of server:\n{0}'.format(status))
    
    # And we have to wait for the server to actually be up and running!
    server_is_starting = datetime.datetime.now()
    while server_is_starting:
        try:
            fetch_rows('SELECT * FROM pg_stat_activity;')
            server_is_starting = False
        except OperationalError:
            if (datetime.datetime.now() - server_is_starting).seconds > time_to_wait:
                server_is_starting = False
                raise Exception('Could not run query on server after {0} seconds. Please investigate.'.format(time_to_wait))
            
    