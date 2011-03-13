from django.db import models

# Create your models here.
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
