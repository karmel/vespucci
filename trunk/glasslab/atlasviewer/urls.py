from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('django.views.generic.simple',
    # Example:
    # (r'^atlasviewer/', include('atlasviewer.foo.urls')),
    ('^$', 'redirect_to', {'url': '/admin/'}),
    
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)
