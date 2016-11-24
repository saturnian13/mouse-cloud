"""Models relating to high-speed video analysis

"""

from __future__ import unicode_literals

from django.db import models

# Import models from the main app
import runner.models

# Create your models here.
class VideoSession(models.Model):
    # Name of the session
    name = models.CharField(max_length=200, primary_key=True)

    # Link it to a behavioral session
    # Not possible to link to multiple behavioral sessions
    # Probably this would be handled by creating redundant
    # VideoSessions
    bsession = models.ForeignKey(runner.models.Session)
