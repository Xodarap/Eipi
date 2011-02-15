# Create your views here.
from eipi2.gina.models import Sex
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader
from eipi2.feeds.models import Story
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core import serializers
from django.utils import simplejson
from django.db.models.query import QuerySet
from eipi2.feeds.addFeeds import addFeeds
from django.http import HttpResponseRedirect

def index(request):
    return render_to_response('gina/index.html', {})

def data(request):    
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(SerializeData.SerializeSex(Sex.objects.all())))
    return r;

class SerializeData:
    @staticmethod
    def SerializeSex(sexObj):
        rows = []
        for obj in sexObj:
            rows.append(obj)
        return rows    