from django.contrib.syndication.views import Feed
from eipi2.feeds.models import Comment

class PetaFeed(Feed):
    item_copyright = "Copyright (c) 2011, Ben West"

    # Feed-wide settings
    def items(self, keyword):
        return Comment.objects.filter(KeyWord__exact = keyword).order_by('Date').reverse()[:20]

    def get_object(self, request, keyword):
        return keyword

    def link(self, keyword):
        return "http://ei-pi.com/feeds/" + keyword + "/vegfeed"

    def description(self, keyword):
        return "Comments on Reddit referencing " + keyword

    def title(self, keyword):
        return keyword + " chatter"

    # Item-specific settings
    def item_title(self, item):
        if (item.Story != None):
            return item.Story.title
        return item.Content

    def item_description(self, item):
        return item.Content

    def item_link(self, item):
        return item.Url

    def item_pubdate(self, item):
        return item.Date
    
    def item_categories(self, item):
        return item.KeyWord
    
