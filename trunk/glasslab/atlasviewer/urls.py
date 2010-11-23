from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
admin.autodiscover()


urlpatterns = patterns('',
    # Media
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_DOC_ROOT}),
)

urlpatterns += patterns('django.views.generic.simple',
    # Example:
    # (r'^atlasviewer/', include('atlasviewer.foo.urls')),
    ('^$', 'redirect_to', {'url': '/admin/'}),
    
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    
    # Transcript app
    (r'^transcript/', include('glasslab.atlasviewer.transcript.urls')),

)
