from django.template import Context, loader
from eipi2.feeds.models import Story
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core import serializers
from django.utils import simplejson
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from eipi2.UserAnalytics import *
from eipi2.UserAnalytics.models import SiteUser, SubmittedLink, Comment
from eipi2 import UserAnalytics
from eipi2.UserAnalytics.updateUser import userMgmt
from datetime import datetime, timedelta
from django.db.models import Avg, Max, Min, Count
from django.db import connection, transaction
import operator

def index(request):
    return render_to_response('feeds/index.html', {})

# JSON method
def update(request, user_id):
    currentUser = get_object_or_404(SiteUser, pk = user_id)
    userMgmt.update(currentUser)
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(True))        
    return r

# JSON method
def storyData(request, user_id):
    currentUser = get_object_or_404(SiteUser, pk = user_id)
    retData = {}
    for story in SubmittedLink.objects.filter(SiteUser = currentUser,
                                              Date__gte = datetime.now() - timedelta(days = 100)):
        if not retData.has_key(story.SubSite.Name):
            retData[story.SubSite.Name] = []
        retData[story.SubSite.Name].append(StoryUtils.StoryToJson(story))        
    
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(retData))        
    return r

def stories(request, user_id):
    json_url = 'storyaggregation'
    view_data = {'json_url': json_url,
                 'title': 'Submitted Links',
                 'extra_column': 'Avg Comments'
                 }
    return render_to_response('UserAnalytics/Comments.html',view_data)

def commentData(request, user_id):
    currentUser = get_object_or_404(SiteUser, pk = user_id)
    retData = []
    for comment in Comment.objects.filter(SiteUser = currentUser):
        retData.append(CommentUtils.CommentToJson(comment))
    
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(retData))        
    return r 

def storyAggregation(request, user_id):
    currentUser = get_object_or_404(SiteUser, pk = user_id)
    aggregate_data = SubmittedLink.objects.values('SubSite__Name').annotate(
                                            Avg('Votes'), Count('Votes'), Avg('Comments')
                                        )        
    
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(StoryUtils.StoryTable(aggregate_data)))
    return r        

def commentAggregation(request, user_id):
    currentUser = get_object_or_404(SiteUser, pk = user_id)
    aggregate_data = Comment.objects.values('SubSite__Name').annotate(
        Avg('Votes'), Count('Votes'), Avg('Replies')
    )
    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(Comment_Utils.comment_table(aggregate_data)))
    return r


def comments(request, user_id):
    json_url = 'commentaggregation'
    view_data = {'json_url': json_url,
                 'title': 'Comments',
                 'extra_column': 'Avg Replies'
                 }
    return render_to_response('UserAnalytics/Comments.html', view_data)

def graph(request, user_id):
    return render_to_response('UserAnalytics/Graph.html')

# JSON Method
def graph_data(request, user_id):
    cursor = connection.cursor()

    cmd = """
    select sum(sum1) as s1, sum(sum2), sum(sum3), sum(sum4), sum(sum5), sum(sum6), sum(sum7) from (
    SELECT 
    (CASE WHEN `{0}` <= CurDate() - 0 THEN Votes ELSE 0 END) as sum1,
    (CASE WHEN `{0}` <= CurDate() - 1 THEN Votes ELSE 0 END) as sum2,
    (CASE WHEN `{0}` <= CurDate() - 2 THEN Votes ELSE 0 END) as sum3,
    (CASE WHEN `{0}` <= CurDate() - 3 THEN Votes ELSE 0 END) as sum4,
    (CASE WHEN `{0}` <= CurDate() - 4 THEN Votes ELSE 0 END) as sum5,
    (CASE WHEN `{0}` <= CurDate() - 5 THEN Votes ELSE 0 END) as sum6,
    (CASE WHEN `{0}` <= CurDate() - 6 THEN Votes ELSE 0 END) as sum7
    from {1}
    ) as t
    """
    # Comments
    cursor.execute(cmd.format('Date', "UserAnalytics_comment"))
    row = cursor.fetchone()
    cleanedComments = map(int, row)
    
    # Stories
    cursor.execute(cmd.format('Date', "UserAnalytics_submittedlink"))
    row = cursor.fetchone()
    cleanedStories = map(int, row)

    data = { "Comments" : cleanedComments,
             "Stories"  : cleanedStories
             }

    r = HttpResponse(mimetype='application/json')
    r.write(simplejson.dumps(data))
    return r

'''
class StoryUtils:
    # Converts a story into a JSON-Serializable object
    
    @staticmethod
    def StoryToJson(story):
        return {
                'Url': story.Url,
                'Votes': story.Votes,
                'Comments': story.Comments,
                'Date': story.Date.strftime('%Y-%m-%dT%H:%M:%S'),
                'Title': story.Title,
                'PermaLink': story.PermaLink,
                'Site': story.SubSite.Site.Name,
                'SubSite': story.SubSite.Name
                }
'''    
class Comment_Utils:
    @staticmethod
    def CommentToJson(comment):
        return {
                'Id':       comment.Id,
                'Votes':    comment.Votes,
                'SubSite':  comment.SubSite.Name,
                'Site':     comment.SubSite.Site.Name,
                'Date':     comment.Date.strftime('%Y-%m-%dT%H:%M:%S'),
                'Text':     comment.Text,
                'Replies':  comment.Replies
                }    
    
    @staticmethod
    def comment_table(aggregate_data):
        rows = map(Comment_Utils.comment_to_row, aggregate_data)
        return {'page': 1,
                'total':1,
                'items': len(rows),
                'rows': rows}

    @staticmethod
    def comment_to_row(comment):
        cellData = [
            comment['SubSite__Name'],
            comment['Votes__count'],
            comment['Votes__avg'],
            comment['Replies__avg']
            ]
        return {
            'id': comment['SubSite__Name'],
            'cell': cellData
                }

class StoryUtils:
    @staticmethod
    def StoryTable(aggregate_data):
        rows = map(StoryUtils.storyToRow, aggregate_data)
        return {'page': 1,
                'total':1,
                'items': len(rows),
                'rows': rows}
    
    @staticmethod
    def storyToRow(comment):
        cellData = [
            comment['SubSite__Name'],
            comment['Votes__count'],
            comment['Votes__avg'],
            comment['Comments__avg']
            ]
        return {
            'id': comment['SubSite__Name'],
            'cell': cellData
            }
