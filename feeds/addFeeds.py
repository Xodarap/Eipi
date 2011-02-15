import sys
import MySQLdb
import feedparser
import datetime
import simplejson
import urllib2
from datetime import timedelta
from eipi2.feeds.models import Story, Source
from django.utils.html import strip_tags
from eipi2.feeds.FeedFilter import feedFilter

# Gets all the stories from the defined feeds table
class addFeeds:
    @staticmethod
    def addFeed(feedUrl, category):
        filter = feedFilter()
        if (feedUrl.endswith('.xml')):
            addFeeds.addXmlFeed(feedUrl, category, filter)
        elif (feedUrl.endswith('.json')):
            addFeeds.addJsonFeed(feedUrl, category, filter)
        
    @staticmethod    
    def addXmlFeed(feedUrl, category, filter): 
        feed = feedparser.parse(feedUrl) 
        numAdded = 0
        for entry in feed['entries']:
            try:
                href = entry.links[0].href
                story, created = Story.objects.get_or_create(Url = href[0:199],
                                            defaults = {
                                                        'title': strip_tags(entry.title),
                                                        'AddedTime': datetime.datetime.now(),
                                                        'valid': False,
                                                        'category': category,
                                                        'source': feedUrl
                                                        })
                if (created):
                    story.save()
                    numAdded = numAdded + 1
                    filter.Train(story) # Pass to the bayes filter
                    
            except Exception as e:
                story = e

    # Only supports Reddit JSON atm                
    @staticmethod
    def addJsonFeed(feedUrl, category, filter):
        req = urllib2.Request(feedUrl)
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = simplejson.load(f)        
        for entry in data['data']['children']:
            storyData = entry['data']
            url = "http://www.reddit.com" + storyData['permalink']
            #url = [ch for ch in url if ord(ch) < 128]
            url = url[0:199]            
            try:
                story, created = Story.objects.get_or_create(Url = url,
                                            defaults = {
                                                        'title': strip_tags(storyData['title']),
                                                        'AddedTime': datetime.datetime.now(),
                                                        'valid': False,
                                                        'category': category,
                                                        'source': feedUrl
                                                        })
                story.Ups = storyData['ups']
                story.Downs = storyData['downs']
                story.save()
            
                if(created):
                    filter.Train(story)
            except:
                pass
    @staticmethod
    def addAllFeeds():
        waitTime = timedelta(minutes = 5)
        for src in Source.objects.filter(LastGet__lt = (datetime.datetime.now() - waitTime)):
            if src == None:
                break;
            addFeeds.addFeed(src.Url, src.Category)
            src.LastGet = datetime.datetime.now()
            src.save()
        #h = feedFilter()
        #h.Train()    