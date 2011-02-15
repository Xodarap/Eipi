from spambayes import mboxutils
from spambayes import hammie
from eipi2.feeds.models import Story
def test():
    msg =      """From god@heaven.af.mil Sat Jan  3 01:05:34 1996
               Return-Path: <god@heaven.af.mil>
               Delivered-To: djb@silverton.berkeley.edu
               Date: 3 Jan 1996 01:05:34 -0000
               From: a@b.com
               To: djb@silverton.berkeley.edu (D. J. Bernstein)

               How's that mail system project coming along?
               
               """
    msg = "test"
    h = hammie.open('/tmp/hammieTemp', 'dbm', 'c')           
    h.train(msg, True)
    print(h.score(msg,True))
    
class feedFilter:
    hammieFile = '/home/eipi/eipi2/hammieData'
    
    def __init__(self):
        self.h = hammie.open(self.hammieFile, mode = 'c')
    
    def TrainAll(self):
        for story in Story.objects.all():
            self.h.train(story.title, story.valid)       
        self.h.store()         
    
    def Train(self, story):
        self.h.train(story.title, story.valid)
        self.h.store()
    
    def UnTrain(self, story):
        self.h.untrain(story.title, story.valid)        
        self.h.store()        
    def Score(self, story, evidence = False):
        return self.h.score(story.title, evidence)
