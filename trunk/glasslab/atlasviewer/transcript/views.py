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
    data = render_to_string('custom_query_export.txt',
                              context,
                              context_instance=RequestContext(request))
    response = HttpResponse(data, mimetype='text/tab-separated-values')
    response['Content-Disposition'] = 'attachment; filename=custom_query_%s.tsv' % randint(0,9999)
    return response
        
def _custom_query(request, limit=10000):
    '''
    DANGEROUS! Accepts custom, raw SQL queries for searches.
    
    Make sure this is accessible by authenticated users only.
    '''
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to view that page.') 
        return redirect('/admin/')
    
    rows, field_names = [], []
    query = request.REQUEST.get('query', '')
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