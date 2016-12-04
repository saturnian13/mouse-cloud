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
    bsession = models.ForeignKey(runner.models.Session, blank=True, null=True)

    # Parameters of the video
    frame_height = models.IntegerField(null=True, blank=True)
    frame_width = models.IntegerField(null=True, blank=True)
    frame_rate = models.FloatField(null=True, blank=True)
    
    # Should probably come from bsession
    # But in case it is different for some reason, allow override here
    bsession_logfilename = models.CharField(max_length=1000, blank=True)
    
    ## Data files
    # These are *relative to the session directory*
    all_edges_filename = models.CharField(max_length=1000, blank=True)
    edge_summary_filename = models.CharField(max_length=1000, blank=True)
    tac_filename = models.CharField(max_length=1000, blank=True)
    whiskers_table_filename = models.CharField(max_length=1000, blank=True)
    clustered_tac_filename = models.CharField(max_length=1000, blank=True)
    colorized_whisker_ends_filename = models.CharField(
        max_length=1000, blank=True)
    contacts_summary_filename = models.CharField(max_length=1000, blank=True)
    colorized_contacts_summary_filename = models.CharField(
        max_length=1000, blank=True)

    # The "raw video", or monitor video
    monitor_video = models.CharField(max_length=1000, blank=True)
    
    # Original matfiles
    # This one is not relative to anything
    matfile_directory = models.CharField(max_length=1000, blank=True)
    
    # Sync
    fit_b2v0 = models.FloatField(null=True, blank=True)
    fit_b2v1 = models.FloatField(null=True, blank=True)
    fit_v2b0 = models.FloatField(null=True, blank=True)
    fit_v2b1 = models.FloatField(null=True, blank=True)
    
    ## Other notes
    whisker_colors = models.CharField(max_length=100, blank=True)
    param_face_choices = ((0, 'left'), (1, 'right'), (2, 'top'), (3, 'bottom'),)
    param_face_side = models.IntegerField(null=True, blank=True,
        choices=param_face_choices,
    )
    
    ## Parameters
    # Relating to edging
    param_edge_lumthresh = models.IntegerField(null=True, blank=True)
    param_edge_split_iters = models.IntegerField(null=True, blank=True,
        default=5)

    param_edge_x0 = models.IntegerField(null=True, blank=True)
    param_edge_x1 = models.IntegerField(null=True, blank=True)
    param_edge_y0 = models.IntegerField(null=True, blank=True)
    param_edge_y1 = models.IntegerField(null=True, blank=True)

    param_edge_crop_x0 = models.IntegerField(null=True, blank=True)
    param_edge_crop_x1 = models.IntegerField(null=True, blank=True)
    param_edge_crop_y0 = models.IntegerField(null=True, blank=True)
    param_edge_crop_y1 = models.IntegerField(null=True, blank=True)
    
    # Relating to follicle
    param_fol_x0 = models.IntegerField(null=True, blank=True)
    param_fol_x1 = models.IntegerField(null=True, blank=True)
    param_fol_y0 = models.IntegerField(null=True, blank=True)
    param_fol_y1 = models.IntegerField(null=True, blank=True)    
    
    def __str__(self):
        return str(self.name)