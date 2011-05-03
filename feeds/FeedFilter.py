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
        url = story.Url if (story.ActualUrl == None) else story.ActualUrl
        try:
            opener = urllib2.build_opener()
            req = urllib2.Request(url)
            f = opener.open(req)
            html = f.read()
            clean = str([x for x in html if (x in range(128))])
            self.train_internal(story, story.title + " " + clean)
        except:
            self.train_internal(story, story.title)

    def Train_on_data(self, story, data):
        self.train_internal(story, data)

    def train_internal(self, story, data):
        self.h.train(data, story.valid)
        self.h.store()
    
    def UnTrain(self, story):
        self.h.untrain(story.title, story.valid)        
        self.h.store()        
    def Score(self, story, evidence = False):
        return self.h.score(story.title, evidence)
