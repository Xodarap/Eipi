from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from eipi2 import UserAnalytics
import UserAnalytics.views

# django cron
import django_cron
django_cron.autodiscover()

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^eipi2/', include('eipi2.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^account/login$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^feeds/$', 'feeds.views.index'),    
    (r'^feeds/storyList$','feeds.views.storyList'),
    (r'^(?P<story_id>\d+)/vote$', 'feeds.views.vote'),
    (r'^(?P<story_id>\d+)/voteup/(?P<should_be_up>[01])', 'feeds.views.vote_up'),
    (r'^feeds/update$', 'feeds.views.update'),
    (r'^feeds/updateAll$', 'feeds.views.updateAll'),
    (r'^feeds/recentstories$', 'feeds.views.recent_stories'),
    (r'^feeds/recentstorydata$', 'feeds.views.recent_stories_data'),
    (r'^feeds/peta$', 'feeds.views.peta'),
    (r'^feeds/petaData$', 'feeds.views.peta_data'),
    (r'^feeds/addComments$', 'feeds.views.add_comments_view'),
    (r'^(?P<comment_id>\d+)/votepeta$', 'feeds.views.vote_peta'),
    
    (r'^useranalytics/(?P<user_id>\d+)/update$', 'UserAnalytics.views.update'),
    (r'^useranalytics/$', 'UserAnalytics.views.index'),
    (r'^useranalytics/(?P<user_id>\d+)/storydata$', 'UserAnalytics.views.storyData'),
    (r'^useranalytics/(?P<user_id>\d+)/stories$', 'UserAnalytics.views.stories'),   
    (r'^useranalytics/(?P<user_id>\d+)/commentdata$', 'UserAnalytics.views.commentData'),    
    (r'^useranalytics/(?P<user_id>\d+)/comments$', 'UserAnalytics.views.comments'),     
    (r'^useranalytics/(?P<user_id>\d+)/commentaggregation', 'UserAnalytics.views.commentAggregation'),
    (r'^useranalytics/(?P<user_id>\d+)/storyaggregation', 'UserAnalytics.views.storyAggregation'),
    (r'^useranalytics/(?P<user_id>\d+)/graph$', 'UserAnalytics.views.graph'),
    (r'^useranalytics/(?P<user_id>\d+)/graphaggregation$', 'UserAnalytics.views.graph_data'),

    (r'^gina/$','gina.views.index'),
    (r'^gina/data$','gina.views.data')    
    
    # This auto-maps 
    #*map(
    #     lambda x: url(r'^myapp/%s/$' % x, x, name='myapp_%s' % x),
    #     [k for k,v in UserAnalytics.views.__dict__.items() if callable(v)]
    # )
)

urlpatterns += patterns('django.views.static',
(r'^static/(?P<path>.*)$', 
    'serve', {
    'document_root': '/home/eipi/webapps/django/eipi2/eipi2/static/',
    'show_indexes': True }),)
