from eipi2.UserAnalytics.models import *
from eipi2.feeds.models import *
import urllib2
import simplejson
import datetime
import logging

class userMgmt:
    @staticmethod
    def update(siteUser):
        if(siteUser.Site.Name == "Reddit"):
            userMgmt.updateReddit(siteUser)
            
    @staticmethod        
    def updateReddit(siteUser):
        userMgmt.updateRedditStories(siteUser)
        userMgmt.updateRedditComments(siteUser)
        #userMgmt.updateRedditLikes(siteUser)
        
    @staticmethod    
    def updateRedditComments(siteUser):
        req = urllib2.Request("http://www.reddit.com/user/" + siteUser.Name + "/comments/.json")
        opener = urllib2.build_opener()
        try:
            f = opener.open(req)
            data = simplejson.load(f)        
            reddit, created = Site.objects.get_or_create(Name = 'reddit')
            reddit.save()

            for comment in data['data']['children']:
                cmtData = comment['data']
                subReddit, created = SubSite.objects.get_or_create(Name = cmtData['subreddit'],
                                                          defaults = {'Site_id' : reddit.id})
                subReddit.Site = reddit
                subReddit.save()
                newComment, created = Comment.objects.get_or_create(Id = cmtData['id'],
                                                                    defaults = { 
                                                                        'SiteUser' : siteUser,
                                                                        'SubSite' : subReddit,
                                                                        'Date' : datetime.datetime.fromtimestamp(cmtData['created']),
                                                                        'Text' : cmtData['body_html']
                                                                    }
                                                                    )
                newComment.Replies = cmtData['replies']
                if(newComment.Replies == ''):
                    newComment.Replies = 0
                newComment.Votes = cmtData['ups'] - cmtData['downs']
                newComment.save()
        except:
            logging.exception('Error updating user - is reddit down?')

        userMgmt.add_bitly('hpGK0b')
        
            # TODO: if(re.search("http://bit\.ly/(?P<hash>.+)\"", cmtData['body_html']).group("hash")
    @staticmethod
    def add_bitly(hash):
        base_url = 'https://api-ssl.bitly.com/v3/clicks?login=xodarap&apiKey=R_c83359ddea209b03313b463317cb3c41&hash='
        req = urllib2.Request(base_url + hash)
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = simplejson.load(f)

        link, created = Links.objects.get_or_create(Hash = hash,
                                    defaults = {'Date': datetime.datetime.now(),
                                                'Clicks': 0})
        link.Clicks = data['data']['clicks'][0]['user_clicks']
        link.save()
                        
    @staticmethod    
    def updateRedditStories(siteUser):    
        req = urllib2.Request("http://www.reddit.com/user/" + siteUser.Name + "/submitted/.json")
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = simplejson.load(f)
        reddit, created = Site.objects.get_or_create(Name = 'reddit')
        
        for story in data['data']['children']:
            if story['kind'] != 't3':  # t3 = story; i'm not sure if this can ever be false?
                continue
            storyData = story['data']
            url = storyData['url']
            permalink = storyData['permalink']
            subReddit, created = SubSite.objects.get_or_create(Name = storyData['subreddit'],
                                                      defaults = {'Site_id' : reddit.id})
            subReddit.Site = reddit
            subReddit.save()
            # Create a new link only if url/siteuser/subsite doesn't exist - not if
            # votes or comments are different
            newObj, created = SubmittedLink.objects.get_or_create(PermaLink = permalink,
                                                         Url = url, 
                                                         SiteUser = siteUser,
                                                         defaults = {'SubSite_id': subReddit.id,
                                                                     'Date': datetime.datetime.fromtimestamp(storyData['created'])})
            newObj.SubSite = subReddit
            newObj.Votes = storyData['ups'] - storyData['downs']
            newObj.Comments = storyData['num_comments']
            newObj.Title = storyData['title']
            newObj.save()

    @staticmethod
    def updateRedditLikes(siteUser):
        req = urllib2.Request("http://www.reddit.com/user/Xodarap/liked/.json")

        opener = urllib2.build_opener()
        f = opener.open(req)
        data = simplejson.load(f)
        reddit, created = Site.objects.get_or_create(Name = 'reddit')
        
        for story in data['data']['children']:
            if story['kind'] == 't3':  # t3 = story; i'm not sure if this can ever be false?
                continue
            storyData = story['data']
            url = storyData['url']
            permalink = storyData['permalink']
            full_link = 'http://www.reddit.com' + permalink
            # If they liked some random crap, we don't care. Only if
            # it's a valid story
            exists = Story.objects.all().filter(Url = full_link, valid = True).count()
            if exists < 1:
                continue
            
            like_obj, created = UserVote.objects.get_or_create(url = full_link, user = siteUser, defaults = { 'Site_id': reddit.id, 'like': True})
            if created:
                like_obj.save()
        
