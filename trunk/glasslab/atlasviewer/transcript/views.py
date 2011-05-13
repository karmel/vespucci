'''
Created on Nov 16, 2010

@author: karmel
'''
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.contrib import messages
from glasslab.utils.database import fetch_rows
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from random import randint
from glasslab.glassatlas.datatypes.transcript import FilteredGlassTranscript
from django.db.models.aggregates import Max
from glasslab.atlasviewer.utilities.models import SavedQuery
from django.template.defaultfilters import urlencode

@login_required
def stored_results(request, id):
    q = SavedQuery.objects.get(id=id)
    field_names, rows = _split_stored_results(q.stored_results)
    context = {'rows': rows,
               'field_names': field_names,
               'stored_query': True, 
               'query': q, }
    return render_to_response('custom_query.html',
                              context,
                              context_instance=RequestContext(request))

@login_required
def stored_results_export(request, id):
    q = SavedQuery.objects.get(id=id)
    field_names, rows = _split_stored_results(q.stored_results)
    context = {'rows': rows,
               'field_names': field_names,
               'stored_query': True, 
               'query': q, }
    return _query_export(request, context)

def _split_stored_results(results):
    '''
    Get cleaned lists from TSV.
    '''
    results = results.split('\n')
    field_names = [(_clean_stored_results(name),) for name in results[0].split('\t')]
    rows = [map(_clean_stored_results,row.split('\t')) for row in results[1:]]
    return field_names, rows

def _clean_stored_results(string):
    ''' 
    Turn stored TSV values into HTML displayables.
    '''
    return string.strip('"').strip().replace('""','"')

@login_required
def custom_query_redirect(request, id):
    q = SavedQuery.objects.get(id=id)
    return HttpResponseRedirect('/transcript/custom_query?query=%s' % urlencode(q.query))

@login_required
def custom_query(request):
    context = _custom_query(request, limit=10000)
    return render_to_response('custom_query.html',
                              context,
                              context_instance=RequestContext(request))

@login_required
def custom_query_export(request):
    context = _custom_query(request, limit=100000)
    return _query_export(request, context)

def _query_export(request, context):
    data = render_to_string('custom_query_export.txt',
                              context,
                              context_instance=RequestContext(request))
    response = HttpResponse(data, mimetype='text/tab-separated-values')
    response['Content-Disposition'] = 'attachment; filename=custom_query_%s.tsv' % randint(0,9999)
    return response

@login_required
def restore_query(request, id):
    if int(id) == 0:
        qs = SavedQuery.objects.filter(id__gte=38).exclude(id__in=[68,69,70]).order_by('-id')
        for q in qs:
            context = _custom_query(request, limit=100000, query=q.query)
            stored_results = _restore_query(request, context)
            q.stored_results = stored_results
            q.save()
        return
    q = SavedQuery.objects.get(id=id)
    context = _custom_query(request, limit=100000, query=q.query)
    stored_results = _restore_query(request, context)
    q.stored_results = stored_results
    q.save()
    return HttpResponseRedirect('/transcript/stored_results/%d/' % q.id)

def _restore_query(request, context):
    data = render_to_string('custom_query_export.txt',
                              context,
                              context_instance=RequestContext(request))
    return data
        
def _custom_query(request, limit=10000, query=None):
    '''
    DANGEROUS! Accepts custom, raw SQL queries for searches.
    
    Make sure this is accessible by authenticated users only.
    '''
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to view that page.') 
        return redirect('/admin/')
    
    rows, field_names = [], []
    query = query or request.REQUEST.get('query', '')
    if query:
        rows, cursor = fetch_rows(query, return_cursor=True, using='read_only')
        field_names = cursor.description

    return {'rows': rows[:limit],
           'field_names': field_names,
           'query': query, 
           'limit': limit, }

def transcripts_ucsc_track_0(request):
    return _transcripts_ucsc_track(request, strand=0)
def transcripts_ucsc_track_1(request):
    return _transcripts_ucsc_track(request, strand=1)

def _transcripts_ucsc_track(request, strand=0):
    return render_to_response('transcripts_ucsc_track_%d.bed' % strand,
                              {},
                              context_instance=RequestContext(request))