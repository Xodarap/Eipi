#!/usr/local/bin/python2.6
import os
import sys

sys.path.append('/home/eipi/webapps/django/eipi2')
sys.path.append('/home/eipi/webapps/django/eipi2/eipi2')
sys.path.append('/home/eipi/webapps/django/eipi2/eipi2/feeds/')
sys.path.append('/home/eipi/webapps/django/eipi2/eipi2/spambayes-1.0.4/spambayes/')
sys.path.append('/home/eipi/webapps/django/eipi2/eipi2/spambayes-1.0.4/')
sys.path.append('/home/eipi/webapps/django')
sys.path.append('/home/eipi/webapps/django/lib/python2.6')
sys.path.append('/home/eipi/webapps/django/lib/python2.6/django/utils/')
sys.path.append('/home/eipi/lib/python2.4/')

from django.core.handlers.wsgi import WSGIHandler
from eipi2.feeds.addFeeds import addFeeds

os.environ['DJANGO_SETTINGS_MODULE'] = 'eipi2.settings'

addFeeds.addAllFeeds()
