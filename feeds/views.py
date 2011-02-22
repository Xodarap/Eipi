from django.template import Context, loader
from eipi2.feeds.models import Story
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core import serializers
from django.utils import simplejson
from django.db.models.query import QuerySet
from eipi2.feeds.addFeeds import addFeeds
from django.http import HttpResponseRedirect
from eipi2.feeds.FeedFilter import feedFilter
from django.db.models import Q
import itertools
import re
import string
import urllib2
from django.core.paginator import Paginator

# Create your views here.
def index(request):
    return render_to_response('feeds/index.html', {})
'''
def storyList(request):
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(storyTable.buildStoryTable(
                                  Story.objects.all().order_by('AddedTime').reverse()
                                                          )))
    return r
'''
def storyList(request):
    rows = int(request.GET.get('rows'))
    page = int(request.GET.get('page'))
    sort_by = request.GET.get('sidx')
    if (sort_by == ''):
        sort_by = 'AddedTime'
    elif (sort_by == 'Votes'):
        sort_by = 'Ups'
    stories = Story.objects.all().order_by(sort_by).reverse()
    if (request.GET.get('sord') == 'desc'):
        stories = stories.reverse()
    paginator = Paginator(stories, rows)
    curPage = paginator.page(page)
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(storyTable.buildStoryTable(curPage.object_list,
                                                        paginator.num_pages,
                                                        page)))
    return r

def vote(request, story_id):
    p = get_object_or_404(Story, pk = story_id)
    filter = feedFilter()
    filter.UnTrain(p)
    p.valid =  not p.valid
    p.save()
    filter.Train(p)
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps({'valid': str(p.valid)}))
    return r

def vote_up(request, story_id, should_be_up):
    p = get_object_or_404(Story, pk = story_id)
    p.VoteUp = should_be_up
    p.save()
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps({'VoteUp': str(p.VoteUp)}))
    return r    

def update(request):
    addFeeds.addAllFeeds()
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(True))
    return r
    #return HttpResponseRedirect('/feeds')

def updateAll(request):
    for story in Story.objects.filter(Url__contains = 'http://www.reddit.com').filter(
                                              Q(Ups__isnull = True) | Q(Downs__isnull = True)):        
        req = urllib2.Request(story.Url + '.json')
        try:
            f = urllib2.build_opener().open(req)
            data = simplejson.load(f)      
            storyData = data[0]['data']['children'][0]['data']
            story.Ups = storyData['ups']
            story.Downs = storyData['downs']
            story.save()
        # sometimes we truncate the url. So the request might fail    
        except:
            pass
    return HttpResponseRedirect('/feeds')

def recent_stories(request):
    return render_to_response('feeds/to_vote_on.html')

# JSON method
def recent_stories_data(request):
    stories  = Story.objects.filter(valid = True).filter(Ups__isnull = False).order_by('AddedTime').reverse()[0:10]
    cleaned = map(story_to_html, stories);
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(cleaned))
    return r    

def story_to_html(story):
    title ='Vote this story ' + ('up' if story.VoteUp else 'down')
    css_class = 'thumbsUp' if story.VoteUp else 'thumbsDown'
    icon = '<span class="icon ' + css_class + '" title="' + title +'">&nbsp;</span>'
    link = '<a href="' + story.Url + '" title="' + story.title + '">' + story.title[0:100] + '</a>'
    return icon + link

class storyTable:
    @staticmethod
    def buildStoryTable(stories, maxPages, curPage):
        dict = {'page': curPage,
                'total':maxPages
                }    
        rows = []
        cnt = 0;
        h = feedFilter()
        for story in stories:
            cnt += 1
            score, evidence = h.Score(story, True)
            cleansed = storyTable.understandEvidence(evidence)
            score = "%.2f" % score
            votes = ''
            if (story.Ups != None and story.Downs != None):
                votes = story.Ups - story.Downs
            rows.append({'id': story.id,
                         'cell':
                            [str(story.AddedTime.day),
                             story.category,
                             storyTable.addLink(story.Url, story.title),
                             storyTable.addCheckbox(story.id, story.valid, 'toggleValid'),
                             storyTable.addCheckbox(story.id, story.VoteUp,'toggleVote'),
                             score,
                             votes   
                             ]
                        })
        dict['items'] = cnt
        dict['rows'] = rows
        return dict

    @staticmethod
    def addCheckbox(story_id, checked, method):
        return '<input type="checkbox" onclick="eipi.' + method +'(' + str(story_id) + ')" ' + ('checked="checked"' if checked else '') + ' class="turnIntoCheckbox"/>'

    @staticmethod
    def addLink(url, title):
        cleanTitle = "".join([ch for ch in title if ord(ch) < 128])
        cleanUrl = "".join([ch for ch in url if ord(ch) < 128])

        return '<a href="' + str(cleanUrl) + '" >' + str(cleanTitle) + '</a>'
    
    # The spambayes thing returns clues in a really weird way
    # this makes it a little easier to understand
    @staticmethod
    def understandEvidence(clues):
        return ''
        #genClues = storyTable.filterEvidence(clues)
        #return list(itertools.islice(genClues, 0, 1))
        
    @staticmethod    
    def filterEvidence(clues):    
        #cleaner = re.compile('\\\\\d{2}')
        for clue in clues:
            # there are two special "clues" which are the
            # spam and ham likelihoods. We don't want those
            if clue[0] == '*H*' or clue[0] == '*S*':
                continue
            #str = clue[0]  #.encode('ascii', 'ignore')
            #cleansed = re.sub(r'\x', '', str)
            #yield 'test'
            try:
                yield clue[0].encode('ascii', 'ignore')
            except:
                continue
