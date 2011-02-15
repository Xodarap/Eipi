from django.db import models

class Site(models.Model):
    Name = models.TextField()

class SubSite(models.Model):
    Name = models.TextField()    
    Site = models.ForeignKey('Site')
    
class SiteUser(models.Model):
    Name = models.TextField()
    Site = models.ForeignKey('Site')

class SubmittedLink(models.Model):
    PermaLink = models.URLField(primary_key = True)
    Url = models.URLField()
    Votes = models.IntegerField(null = True)
    Comments = models.IntegerField(null = True)
    SubSite = models.ForeignKey('SubSite')
    SiteUser = models.ForeignKey('SiteUser') 
    Date = models.DateField()
    Title = models.TextField(null = True)

class Comment(models.Model):
    #PermaLink = models.URLField(primary_key = True)
    Id = models.CharField(primary_key = True, max_length = 32)
    Votes = models.IntegerField(null = True)
    SubSite = models.ForeignKey('SubSite')
    SiteUser = models.ForeignKey('SiteUser') 
    Date = models.DateField()
    Text = models.TextField()
    Replies = models.IntegerField(null = True)
    
class UserVote(models.Model):
    site = models.ForeignKey('Site')
    site_user = models.ForeignKey('SiteUser')
    url = models.URLField(db_index = True)
    liked = models.BooleanField()