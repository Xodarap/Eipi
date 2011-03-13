from django_cron import cronScheduler, Job
from eipi2.feeds.addFeeds import addFeeds
from eipi2.feeds.add_comments import add_comments
# Scheduled tasks

class UpdateFeeds(Job):
    # run every hour
    run_every = 3600
    def job(self):
        addFeeds.addAllFeeds()
        add_comments.add_comments()

cronScheduler.register(UpdateFeeds)
