import sys
import MySQLdb
import feedparser
import datetime
import simplejson
import urllib2
import logging
from datetime import timedelta
from eipi2.feeds.models import Story, Source
from django.utils.html import strip_tags
from eipi2.feeds.FeedFilter import feedFilter
from urllib2 import HTTPError

# Gets all the stories from the defined feeds table
class addFeeds:
    @staticmethod
    def addFeed(feedUrl, category):
        filter = feedFilter()
        if (feedUrl.endswith('.xml')):
            addFeeds.addXmlFeed(feedUrl, category, filter)
        elif (feedUrl.endswith('.json')):
            addFeeds.addJsonFeed(feedUrl, category, filter)

    #adds a single XML (RSS) feed
    @staticmethod    
    def addXmlFeed(feedUrl, category, filter): 
        feed = feedparser.parse(feedUrl) 
        numAdded = 0
        map(lambda x: addFeeds.singleXml(x, filter, category, feedUrl), feed['entries'])

    #Parses a single RSS entry
    @staticmethod
    def singleXml(entry, filter, category, feedUrl):
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
            filter.Train(story) # Pass to the bayes filter
            


    # Only supports Reddit JSON atm                
    @staticmethod
    def addJsonFeed(feedUrl, category, filter):
        req = urllib2.Request(feedUrl)
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = simplejson.load(f)
        map(lambda x: addFeeds.singleJson(x, category, filter, feedUrl), data['data']['children'])

    @staticmethod
    def singleJson(entry, category, filter, feedUrl):
        storyData = entry['data']
        url = "http://www.reddit.com" + storyData['permalink']
        url = url[0:199]            

        story, created = Story.objects.get_or_create(Url = url,
                                    defaults = {
                                                'title': strip_tags(storyData['title']),
                                                'AddedTime': datetime.datetime.now(),
                                                'valid': False,
                                                'category': category,
                                                'source': feedUrl,
                                                'ActualUrl': storyData['url']
                                                })
        story.Ups = storyData['ups']
        story.Downs = storyData['downs']
        story.save()

        if(created):
            filter.Train(story)

            
    # Main action. Loops through the db to add all relevant feeds
    # Doesn't add stuff more frequently than once ever 5 min to prevent
    # runaway daemons
    @staticmethod
    def addAllFeeds():
        #addFeeds.retrain()
        waitTime = timedelta(minutes = 5)
        for src in Source.objects.filter(LastGet__lt = (datetime.datetime.now() - waitTime)):
            if src == None:
                break
            addFeeds.addFeed(src.Url, src.Category)
            src.LastGet = datetime.datetime.now()
            src.save()
        #h = feedFilter()
        #h.Train()    

    # Retrains the bayesian filter on all the data
    @staticmethod
    def retrain():
        h = feedFilter()
        h.TrainAll()

    # Updates the actual urls of reddit stories (i.e. the urls of
    # the story itself, rather than the reddit page)
    @staticmethod
    def add_actual_urls():
        stories = Story.objects.all().filter(Url__contains = 'reddit.com', ActualUrl__exact = None)
        map(addFeeds.add_single, stories)

    # Updates the actual url for one story
    @staticmethod        
    def add_single(story):
        story.ActualUrl = addFeeds.actual_url(story.Url)
        story.save()
        
    @staticmethod
    def actual_url(reddit_url):
        opener = urllib2.build_opener()
        # If the url is invalid, then skip it
        try:
            req = urllib2.Request(reddit_url + '.json')
            f = opener.open(req)
            data = simplejson.load(f)
            return data[0]['data']['children'][0]['data']['url']
        # If there's a 503, then that means that the site's down or something,
        # so try again later. But if the URL is malformed, then give up
        except HTTPError, e:
            if e.code == 503:
                return None
            else:
                return ''
        except UnicodeEncodeError, e:
            return ''

        
