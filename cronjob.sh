#!/bin/bash
PYTHONPATH=/home/eipi/webapps/django:/home/eipi/webapps/django/lib/python2.6:/home/eipi/webapps/django/lib/python2.6/django/utils/:/home/eipi/lib/python2.4/:/home/eipi/webapps/django/eipi2/eipi2/spambayes-1.0.4/spambayes/:/home/eipi/webapps/django/eipi2/eipi2/spambayes-1.0.4/:/home/eipi/webapps/django/eipi2:/home/eipi/webapps/django/eipi2/eipi2:/home/eipi/webapps/django/eipi2/eipi2/feeds

DJANGO_SETTINGS_MODULE=eipi.settings

python2.6 cronjob.py