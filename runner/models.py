"""Models for objects in the runner database.

Note: avoid using nullable charfields throughout. This creates two
possible values for NULL: Null/None, and ''. The django convention is to use
''. Other code will interpret '' as equivalent to "not specified", so
do not attempt to store the empty string as a meaningful value.

At the moment all C parameters are required to be CharFields because they
need to be strings, but perhaps it would be better to have allow other types
(eg BooleanField) and then convert before writing to the Autosketch.
"""

from __future__ import unicode_literals

import datetime
from django.db import models
from taggit.managers import TaggableManager

def get_latest_daily_plan():
    return None


class BehaviorCage(models.Model):
    """Cage for holding mice outside of barrier"""
    name = models.CharField(max_length=20, unique=True)
    label_color = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name

class Mouse(models.Model):
    """Mouse, with demographic and training info.
    
    'name' is the training name
    'husbandry_name' is the 'name' field in the main colony database
    
    Some fields are copied in from the main colony database.
    Others relate to how it should be trained.
    Others relate to how its performance should be plotted.
    """
    # Demographic information to be imported from main colony db
    name = models.CharField(max_length=20)
    SEX_CHOICES = ((0, 'M'), (1, 'F'), (2, '?'))
    sex = models.IntegerField(choices=SEX_CHOICES, default=2)
    dob = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)    
    sack_date = models.DateField('sac date', blank=True, null=True)
    
    # We copy these data as a string, rather than creating a cascade
    # of objects. So the data need to be manually synced but not the
    # object model.
    genotype = models.CharField(max_length=200, blank=True)

    # Extra demographic information for behavior
    husbandry_name = models.CharField(max_length=20, null=True, blank=True)
    headplate_color = models.CharField(max_length=10, null=True, blank=True)
    
    # This determines whether to include this mouse in reports, and maybe
    # whether the Runner should include it in the training plan.
    in_training = models.BooleanField(default=False)
    
    # This determine the ones to plot it with in the reports
    training_cohort = models.IntegerField(null=True, blank=True)
    
    # The mouse's cage, used for printing labels
    cage = models.ForeignKey(BehaviorCage, null=True, blank=True)
    
    # Python params
    stimulus_set = models.CharField(max_length=50, blank=True)
    step_first_rotation = models.IntegerField(null=True, blank=True, default=50)
    timeout = models.IntegerField(null=True, blank=True, default=2000)
    scheduler = models.CharField(max_length=50, blank=True)
    max_rewards_per_trial = models.IntegerField(null=True, blank=True, default=1)
    
    # build params
    protocol_name = models.CharField(max_length=50, blank=True)
    script_name = models.CharField(max_length=50, blank=True)
    default_board = models.CharField(max_length=50, null=True, blank=True)
    default_box = models.CharField(max_length=50, null=True, blank=True)

    # Make this an autoslugfield so we can order by it
    @property
    def name_number(self):
        """Return the mouse's number: int(digits in the name)"""
        # Keep the ints
        int_s = filter(lambda c: c in '0123456789', self.name)
        return int(int_s)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return str(self.name)

    @property
    def age(self):
        if self.dob is None:
            return None
        today = datetime.date.today()
        return (today - self.dob).days

    @property
    def sacked(self):
        return self.sack_date is not None

class Box(models.Model):
    """Hardware info about individual boxes"""
    name = models.CharField(max_length=20)
    l_reward_duration = models.IntegerField()
    r_reward_duration = models.IntegerField(null=True, blank=True)
    serial_port = models.CharField(max_length=20)
    video_device = models.CharField(max_length=20, null=True, blank=True)
    
    video_window_position_x = models.IntegerField(null=True, blank=True)
    video_window_position_y = models.IntegerField(null=True, blank=True)
    gui_window_position_x = models.IntegerField(null=True, blank=True)
    gui_window_position_y = models.IntegerField(null=True, blank=True)
    window_position_IR_plot_x = models.IntegerField(null=True, blank=True)
    window_position_IR_plot_y = models.IntegerField(null=True, blank=True)
    subprocess_window_ypos = models.IntegerField(null=True, blank=True)
    
    video_brightness = models.IntegerField(null=True, blank=True)
    video_gain = models.IntegerField(null=True, blank=True)
    video_exposure = models.IntegerField(null=True, blank=True)
    
    @property
    def video_window_position(self):
        return (self.video_window_position_x, self.video_window_position_y)
    @video_window_position.setter
    def video_window_position(self, obj):
        self.video_window_position_x = obj[0]
        self.video_window_position_y = obj[1]

    @property
    def gui_window_position(self):
        return (self.gui_window_position_x, self.gui_window_position_y)
    @gui_window_position.setter
    def gui_window_position(self, obj):
        self.gui_window_position_x = obj[0]
        self.gui_window_position_y = obj[1]

    @property
    def window_position_IR_plot(self):
        return (self.window_position_IR_plot_x, self.window_position_IR_plot_y)        
    @window_position_IR_plot.setter
    def window_position_IR_plot(self, obj):
        self.window_position_IR_plot_x = obj[0]
        self.window_position_IR_plot_y = obj[1]
    
    @property
    def mean_water_consumed(self):
        """Return mean water consumed over last N sessions"""
        return self.session_list[0].name

    def __str__(self):
        return str(self.name)
    
    class Meta:
        ordering = ['name']

class Board(models.Model):
    """Hardware info about individual boards"""
    name = models.CharField(max_length=20)
    
    has_side_HE_sensor = models.BooleanField()
    l_ir_detector_thresh = models.IntegerField(null=True, blank=True)
    r_ir_detector_thresh = models.IntegerField(null=True, blank=True)
    
    # This is both a Python parameter and a C parameter
    # Downstream logic will have to generate '1' for the C parameter
    use_ir_detector = models.NullBooleanField()
    
    # C parameters, need to be strings
    stepper_driver = models.CharField(max_length=10, null=True, blank=True)
    side_HE_sensor_thresh = models.CharField(max_length=10, null=True, blank=True)
    microstep = models.CharField(max_length=10, null=True, blank=True)
    invert_stepper_direction = models.CharField(max_length=10, 
        null=True, blank=True)
    
    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']

class ArduinoProtocol(models.Model):
    """Info about the Arduino protocol, eg TwoChoice.ino"""
    name = models.CharField(max_length=20)
    path = models.CharField(max_length=100)
    
    def __str__(self):
        return str(self.name)

class PythonProtocol(models.Model):
    """Info about the Python code used to interact with an Aruduino protocol"""
    name = models.CharField(max_length=20)
    path = models.CharField(max_length=100)
    
    def __str__(self):
        return str(self.name)

class GrandSession(models.Model):
    """Linked behavioral, opto, neural, video sessions
    
    This is used to store the correspondences between sessions.
    And also can be created online to keep notes before the behavioral
    session is completed.
    
    I would have preferred a FK from GrandSession to each type of session,
    but then the inlines can't be added. It has to be a link from the 
    session to the GrandSession. Made it a OneToOneField because it doesn't
    make much sense to have multiple optosessions per grandsession. Although
    there could be multiple behavioral or video sessions if something
    crashed. Need to deal with that when it comes up.
    """
    name = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    tags = TaggableManager(blank=True)
    
    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['-name']

class Session(models.Model):
    """Info about a single behavioral session"""
    # The name will be constructed from the date, mouse, etc
    name = models.CharField(max_length=200, primary_key=True)
    
    # Which mouse it was
    mouse = models.ForeignKey(Mouse, null=True, blank=True)
    
    # The logfile
    logfile = models.CharField(max_length=200, blank=True)

    # Where it physically took place
    # Note multiple boxes may share the same serial port
    board = models.ForeignKey(Board, null=True, blank=True)
    box = models.ForeignKey(Box, null=True, blank=True)
    
    # This is not necessary because it's part of box
    serial_port = models.CharField(max_length=50, null=True, blank=True)
    
    # The protocol that was run
    autosketch_path = models.CharField(max_length=200, blank=True)
    script_path = models.CharField(max_length=200, blank=True)
    
    # The sandbox where the protocol was compiled
    sandbox = models.CharField(max_length=200, blank=True)
    
    # Protocol parameters
    python_param_scheduler_name = models.CharField(max_length=100,
        verbose_name='Scheduler', null=True, blank=True)
    python_param_stimulus_set = models.CharField(max_length=100,
        verbose_name='StimSet', null=True, blank=True)
    
    # Real-life parameters
    irl_param_stimulus_arm = models.CharField(max_length=100,
        verbose_name='StimArm', null=True, blank=True)
    
    # When it began and ended, maybe other stuff
    date_time_start = models.DateTimeField(null=True, blank=True,
        verbose_name='Start')
    date_time_stop = models.DateTimeField(null=True, blank=True,
        verbose_name='Stop')
    
    # Stuff the user provides
    user_data_water_pipe_position_start = models.FloatField(
        null=True, blank=True, verbose_name='Pipe Start')
    user_data_water_pipe_position_stop = models.FloatField(
        null=True, blank=True, verbose_name='Pipe Stop')
    user_data_left_water_consumption = models.FloatField(null=True, blank=True)
    user_data_right_water_consumption = models.FloatField(null=True, blank=True)
    user_data_left_valve_mean = models.FloatField(null=True, blank=True)
    user_data_right_valve_mean = models.FloatField(null=True, blank=True)
    user_data_left_perf = models.FloatField(null=True, blank=True,
        verbose_name='L perf')
    user_data_right_perf = models.FloatField(null=True, blank=True,
        verbose_name='R perf')
    user_data_bias_summary = models.CharField(max_length=100,
        null=True, blank=True, verbose_name='Bias')
    user_data_weight = models.FloatField(
        null=True, blank=True, verbose_name='Weight')

    # Link to GrandSession
    grand_session = models.OneToOneField(GrandSession, null=True, blank=True)

    def __str__(self):
        if self.name:
            return str(self.name)
        else:
            return 'Unstarted'
    
    def left_valve_summary(self):
        res = ''
        if self.user_data_left_water_consumption:
            res += '%0.2f' % self.user_data_left_water_consumption
        if self.user_data_left_valve_mean:
            res += u' @%0.1f \N{GREEK SMALL LETTER MU}L' % (
                1000 * self.user_data_left_valve_mean)
        return res
    left_valve_summary.short_description = 'L water'

    def right_valve_summary(self):
        res = ''
        if self.user_data_right_water_consumption:
            res += '%0.2f' % self.user_data_right_water_consumption
        if self.user_data_right_valve_mean:
            res += u' @%0.1f \N{GREEK SMALL LETTER MU}L' % (
                1000 * self.user_data_right_valve_mean)
        return res
    right_valve_summary.short_description = 'R water'
    
    def display_left_perf(self):
        try:
            return '%.0f' % (100 * self.user_data_left_perf)
        except:
            return 'NA'
    display_left_perf.short_description = 'L perf'

    def display_right_perf(self):
        try:
            return '%.0f' % (100 * self.user_data_right_perf)
        except:
            return 'NA'
    display_right_perf.short_description = 'R perf'
    
class OptoSession(models.Model):
    """Parameters for optogenetic stimulation during a behavioral session
    
    Seems like this will always be OneToOne with Session. But this is
    an optional link, in case at some point we link these things differently.
    """
    grand_session = models.OneToOneField(GrandSession, null=True, blank=True)
    behavioral_session = models.OneToOneField(Session, null=True, blank=True)
    target = models.CharField(max_length=50, blank=True)
    start_power = models.FloatField(null=True, blank=True)
    stop_power = models.FloatField(null=True, blank=True)
    wavelength = models.FloatField(null=True, blank=True, default=593.5)
    target_orientation = models.CharField(max_length=50, blank=True)
    fiber_diameter = models.FloatField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    sham = models.NullBooleanField(null=True, blank=True)
    
    @property
    def info(self):
        """Short descriptive string"""
        res = 'sham' if self.sham else ''
        if self.start_power:
            res += ' %dmW' % self.start_power
        
        if res == '':
            res = 'NA'
        
        return res