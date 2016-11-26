from __future__ import unicode_literals

from django.db import models

# Create your models here.

# Import models from the main app
import runner.models

# Create your models here.
class NeuralSession(models.Model):
    # Name of the session
    name = models.CharField(max_length=200)

    # Sort name
    # Perhaps better to have a separate object for each sort?
    # Keep it simple for now by having one sort per NeuralSession
    sort_name = models.CharField(max_length=200, default='sort', blank=True)

    # Link it to a behavioral session
    bsession = models.ForeignKey(runner.models.Session)

    ## Data files
    # These are *relative to the session/sort directory*
    kwik_filename = models.CharField(max_length=100, blank=True, 
        default='exp.kwik')
    kwx_filename = models.CharField(max_length=100, blank=True, 
        default='exp.kwx')
    
    ## Sync
    fit_n2b0 = models.FloatField(null=True, blank=True)
    fit_n2b1 = models.FloatField(null=True, blank=True)
    fit_b2n0 = models.FloatField(null=True, blank=True)
    fit_b2n1 = models.FloatField(null=True, blank=True)
    
    ## Parameters
    # TODO: some way of keeping track of broken channels, ie channels that
    # were removed before sorting
    
    # TODO: keep track of house light, backlight, opto, sync channels here