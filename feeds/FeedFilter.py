from spambayes import mboxutils
from spambayes import hammie
from eipi2.feeds.models import Story
import urllib2
import simplejson
    
class feedFilter:
    hammieFile = '/home/eipi/webapps/django/eipi2/eipi2/hammieData'
    
    def __init__(self):
        self.h = hammie.open(self.hammieFile, mode = 'c')
        pass
    
    def TrainAll(self):
        for story in Story.objects.all():
            self.train_internal(story)       
        self.h.store()         
    
    def Train(self, story):
        self.train_internal(story)
        self.h.store()

    def train_internal(self, story):
        url = story.Url
        opener = urllib2.build_opener()

        # This could be a pointer to the reddit story, in which case we'd
        # like to parse the data from the actual page, not reddit
        if "reddit.com" in url:
            redreq = urllib2.Request(url + ".json")
            data = opener.open(redreq)
            json_data = simplejson.load(data)
            url = json_data[0]['data']['children'][0]['data']['url']
            
        req = urllib2.Request(url)
        f = opener.open(req)
        html = f.read()
        clean = str([x for x in html if (x in range(128))])
        self.h.train(story.title + " " + clean, story.valid)
    
    def UnTrain(self, story):
        self.h.untrain(story.title, story.valid)        
        self.h.store()        
    def Score(self, story, evidence = False):
        return self.h.score(story.title, evidence)
       
