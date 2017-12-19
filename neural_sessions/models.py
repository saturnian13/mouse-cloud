from __future__ import unicode_literals

from django.db import models

# Create your models here.

# Import models from the main app
import runner.models

# Create your models here.
class NeuralSession(models.Model):
    # Name of the session
    # Not sure if this should be "DATE_MOUSENAME" or folder name of data
    name = models.CharField(max_length=200)
    
    # Folder name of data
    data_directory = models.CharField(max_length=200, blank=True)
    
    # Online notes
    notes = models.TextField(blank=True)

    # Deprecated
    # Recording number, if there is only one
    recording_number = models.IntegerField(null=True, blank=True,
        help_text='main recording number to analyze (deprecated)')

    # Comma separated list of recording numbers to sort together
    # So if there are separte recordings 1,2 then concatenate these
    # Probably also need a way to deal with a single recording consisting
    # of multiple epochs
    recording_numbers = models.CharField(max_length=20, blank=True,
        help_text='comma separated list of included recording numbers')

    # Sort name
    # Probably this means "the sort to use for data analysis", because
    # multiple sorts may exist.
    sort_name = models.CharField(max_length=200, blank=True)


    ## Links
    # Link it to a behavioral session
    bsession = models.ForeignKey(runner.models.Session, null=True, blank=True)

    # Link to GrandSession
    grand_session = models.OneToOneField(
        runner.models.GrandSession, null=True, blank=True)

    
    ## Online notes
    # e.g., ON4
    adapter = models.CharField(max_length=30, blank=True)
    electrode = models.CharField(max_length=30, blank=True)
    
    # comma separated list
    exclude_channels = models.CharField(max_length=100, blank=True,
        help_text='Comma separated list of broken channels (Sorted order)',
    )
    
    channel_quality_notes = models.TextField(blank=True,
        help_text='Notes on quality of channels (artefacts, noise levels, '
        'good SUs, etc.',
    )

    manipulator_angle = models.FloatField(null=True, blank=True,
        help_text='Angle of the manipulator from vertical'
    )
    
    ain_backlight = models.IntegerField(null=True, blank=True, default=0,
        help_text='0-based AIN channel number of backlight signal (add to 71)'
    )

    ain_opto = models.IntegerField(null=True, blank=True, default=1,
        help_text='0-based AIN channel number of opto signal (add to 71)'
    )
    
    z_touch = models.FloatField(null=True, blank=True,
        help_text='Height of manipulator at initial touch'
    )
    
    z_final = models.FloatField(null=True, blank=True,
        help_text='Height of manipulator at final depth'
    )

    z_withdraw = models.FloatField(null=True, blank=True,
        help_text='Height of manipulator at withdrawal'
    )

    ## Data files
    # These are *relative to the session/sort directory*
    kwik_filename = models.CharField(max_length=100, blank=True)
    kwx_filename = models.CharField(max_length=100, blank=True)
    
    
    ## Sync
    fit_n2b0 = models.FloatField(null=True, blank=True)
    fit_n2b1 = models.FloatField(null=True, blank=True)
    fit_b2n0 = models.FloatField(null=True, blank=True)
    fit_b2n1 = models.FloatField(null=True, blank=True)
    
    ## Parameters
    # TODO: some way of keeping track of broken channels, ie channels that
    # were removed before sorting
    
    # TODO: keep track of house light, backlight, opto, sync channels here