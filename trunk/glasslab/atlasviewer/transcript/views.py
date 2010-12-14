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
from django.http import HttpResponse
from random import randint
from glasslab.glassatlas.datatypes.transcript import FilteredGlassTranscript
from django.db.models.aggregates import Max

@login_required
def custom_query(request):
    context = _custom_query(request)
    return render_to_response('custom_query.html',
                              context,
                              context_instance=RequestContext(request))

@login_required
def custom_query_export(request):
    context = _custom_query(request)
    data = render_to_string('custom_query_export.txt',
                              context,
                              context_instance=RequestContext(request))
    response = HttpResponse(data, mimetype='text/tab-separated-values')
    response['Content-Disposition'] = 'attachment; filename=custom_query_%s.tsv' % randint(0,9999)
    return response
        
def _custom_query(request):
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

    return {'rows': rows,
           'field_names': field_names,
           'query': query, }

def transcripts_ucsc_track(request):
    transcripts = FilteredGlassTranscript.objects.order_by('chromosome__id',
                                                           'transcription_start',
                                                           '-transcription_end').iterator()
    max_score = FilteredGlassTranscript.objects.aggregate(max=Max('score'))['max']
    output = render_to_string('transcripts_ucsc_track.bed',
                              {'transcripts': transcripts,
                               'max_score': max_score},
                              context_instance=RequestContext(request))
    f = file.open('/Users/karmel/Desktop/transcripts_ucsc_track.bed','w')
    f.write(output)
    f.close()
    