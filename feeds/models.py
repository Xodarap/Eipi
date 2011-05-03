from django.db import models

class Story(models.Model):
    Url = models.URLField()
    AddedTime = models.DateTimeField()
    title = models.TextField(null = True)
    valid = models.NullBooleanField()
    category = models.TextField(null = True)
    source = models.TextField(null = True)
    Ups = models.IntegerField(null = True)
    Downs = models.IntegerField(null = True)
    VoteUp = models.NullBooleanField()
    ActualUrl = models.URLField(null = True)
    
    def __unicode__(self):
        return self.title

class Source(models.Model):
    Url = models.URLField()
    LastGet = models.DateTimeField()
    Category = models.TextField()
    
    def __unicode__(self):
        return self.Url
    
class Comment(models.Model):
    Url = models.URLField()
    Date = models.DateTimeField()
    Content = models.TextField()
    KeyWord = models.TextField()
    Story = models.ForeignKey('Story', null = True)
    Valid = models.NullBooleanField()
    OnReddit = models.NullBooleanField()

class Tracker(models.Model):
    Id = models.CharField(max_length = 4, db_index = True, null = True)
    RootUrl = models.URLField(db_index = True)
    IntId = models.AutoField(primary_key = True)
    

'''
class Error(models.Model):
    Date = models.DateTimeField()
    Message = models.TextField()
'''    
