from django.contrib import admin
from .models import Mouse, Box, Board, ArduinoProtocol, \
    PythonProtocol, Session, BehaviorCage, OptoSession, GrandSession
from suit.admin import SortableModelAdmin
from whisk_video.admin import VideoSessionInline
from neural_sessions.admin import NeuralSessionInline

## Filtering by tagging
# https://djangosnippets.org/snippets/2807/
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from taggit.models import TaggedItem 

class TaggitListFilter(SimpleListFilter):
  """
  A custom filter class that can be used to filter by taggit tags in the admin.
  """

  # Human-readable title which will be displayed in the
  # right admin sidebar just above the filter options.
  title = _('tags')

  # Parameter for the filter that will be used in the URL query.
  parameter_name = 'tag'
  
  def lookups(self, request, model_admin):
    """
    Returns a list of tuples. The first element in each tuple is the coded value
    for the option that will appear in the URL query. The second element is the
    human-readable name for the option that will appear in the right sidebar.
    """
    list = []
    tags = TaggedItem.tags_for(model_admin.model)
    for tag in tags:
      list.append( (tag.name, _(tag.name)) )
    return list    

  def queryset(self, request, queryset):
    """
    Returns the filtered queryset based on the value provided in the query
    string and retrievable via `self.value()`.
    """
    if self.value():
      return queryset.filter(tags__name__in=[self.value()])

class BoxAdmin(admin.ModelAdmin):
    list_display = ['name', 'l_reward_duration', 'r_reward_duration', 
        'serial_port', ]#'mean_water_consumed']

class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'stepper_driver', 'use_ir_detector',
        ]

class SessionInline(admin.TabularInline):
    model = Session
    extra = 1
    fields = ('mouse', 'board', 'box',
        'python_param_scheduler_name',
        'python_param_stimulus_set',
        'irl_param_stimulus_arm',
        )

class BehavioralSessionInline(admin.StackedInline):
    """For a tab within GrandSession"""
    model = Session
    fields = ('name', 'mouse', 'board', 'box', 
        'date_time_start', 'date_time_stop',
        'python_param_scheduler_name', 'python_param_stimulus_set',
        'irl_param_stimulus_arm',
        'user_data_water_pipe_position_start',
        'user_data_water_pipe_position_stop',
        'user_data_left_water_consumption',
        'user_data_right_water_consumption',
        'user_data_left_valve_mean',
        'user_data_right_valve_mean',
        'user_data_weight',
        'logfile', 'autosketch_path', 'script_path', 'sandbox',
    )
    
    suit_classes = 'suit-tab suit-tab-behavior'

class OptoSessionInline(admin.StackedInline):
    """Inlined information about OptoSession in a behavioral Session"""
    model = OptoSession
    
    # If fields unspecified, all will be shown
    #~ fields = ('notes', 'sham', 'target', 'target_orientation',
        #~ 'start_power', 'stop_power', 'wavelength', 'fiber_diameter',
    #~ )
    
    # Put it on the opto tab
    suit_classes = 'suit-tab suit-tab-opto'

class GrandSessionAdmin(admin.ModelAdmin):
    """Admin interface for linked sessions
    
    Each type of session gets its own tab. This is useful for creating
    the sessions and taking notes online (before the behavioral session
    is completed).
    
    The list view is used to get a general sense of which sessions are
    available for each type of analysis (neural data, opto, etc).
    """
    # Fields separated by tabs
    fieldsets = [
        ('General', {
            'classes': ('suit-tab', 'suit-tab-general',),
            'fields': [
                'name', 'notes', 'tags',
            ],
        }),
    ]

    # Tabs
    suit_form_tabs = (
        ('general', 'General'),
        ('behavior', 'Behavior'),
        ('opto', 'Opto'),
        ('video', 'Video'),
        ('neural', 'Neural'),
    )    

    # List view
    list_display = [
        'name',
        'tag_list',
        'notes',
        'videosession', 
        'videosession__notes',
        'neuralsession__name', 
        'neuralsession__notes',
        'optosession__info', 
        'optosession__notes',
        'behavioralsession__name',
    ]
    
    list_filter = [
        'session__mouse',
        TaggitListFilter,
    ]
    
    
    ## Callables for the list display (usual __ syntax doesn't work here)
    def neuralsession__name(self, obj):
        return obj.neuralsession.name
    neuralsession__name.short_description = 'neural'

    def behavioralsession__name(self, obj):
        return obj.session.name
    behavioralsession__name.short_description = 'behavior'

    def videosession__notes(self, obj):
        return obj.videosession.notes
    videosession__notes.short_description = 'video notes'
    
    def neuralsession__notes(self, obj):
        return obj.neuralsession.notes
    neuralsession__notes.short_description = 'neural notes'
    
    def optosession__info(self, obj):
        return obj.optosession.info
    optosession__info.short_description = 'opto'
    
    def optosession__notes(self, obj):
        return obj.optosession.notes
    optosession__notes.short_description = 'opto notes'
    
    #~ list_filter = ['mouse', 'board', 'box']
    #~ ordering = ['-date_time_start']
    
    inlines = [OptoSessionInline, VideoSessionInline, NeuralSessionInline,
        BehavioralSessionInline]
    
    # Tagging
    # https://django-taggit.readthedocs.io/en/latest/admin.html
    def get_queryset(self, request):
        return super(GrandSessionAdmin, self).get_queryset(
            request).prefetch_related('tags')
    
    def tag_list(self, obj):
        return ", ".join([o.name for o in obj.tags.all()])

class SessionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Session parameters', {
            'classes': ('suit-tab', 'suit-tab-behavior',),
            'fields': ['name', 'mouse', 'board', 'box', 
                'date_time_start', 'date_time_stop',
                'python_param_scheduler_name', 'python_param_stimulus_set',
                'irl_param_stimulus_arm',
                'grand_session',
            ],
        }),
        ('User-provided data', {
            'classes': ('suit-tab', 'suit-tab-behavior',),
            'fields': [
                'user_data_water_pipe_position_start',
                'user_data_water_pipe_position_stop',
                'user_data_left_water_consumption',
                'user_data_right_water_consumption',
                'user_data_left_valve_mean',
                'user_data_right_valve_mean',
                'user_data_weight',
            ],
        }),
        ('Filenames', {
            'classes': ('suit-tab', 'suit-tab-filenames',),
            'fields': ['logfile', 'autosketch_path', 'script_path', 'sandbox',
            ],
        }),        
    ]

    suit_form_tabs = (
        ('behavior', 'Behavior'),
        ('filenames', 'Filenames'),
    )
    
    list_display = ['date_time_start', 'mouse', 'board', 'box',
        'python_param_scheduler_name',
        'python_param_stimulus_set',
        'user_data_weight',
        'user_data_water_pipe_position_stop',
        'display_left_perf',
        'display_right_perf',
        'left_valve_summary',
        'right_valve_summary',
        'user_data_bias_summary',
        ]
    
    list_filter = ['mouse', 'board', 'box']
    ordering = ['-date_time_start']

class MouseAdmin(admin.ModelAdmin):
    list_display = [
        'husbandry_name', 'name', 'number', 'in_training', 'training_cohort', 
        'stimulus_set',
        'dob', 'notes', 'sack_date', 'genotype', 'headplate_color', 'cage',
    ]
    ordering = ['-in_training', 'number']
    list_editable = ['in_training', 'training_cohort']
    
    list_filter = ['experimenter', 'in_training']

class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ['date_time_start']
    inlines = [SessionInline]

class OptoSessionAdmin(admin.ModelAdmin):
    model = OptoSession
    list_display = ['behavioral_session', 'sham', 
        'target', 'target_orientation',
        'start_power', 'stop_power', 'notes',
    ]
    list_editable = ['notes',]

admin.site.register(Mouse, MouseAdmin)
admin.site.register(Box, BoxAdmin)
admin.site.register(Board, BoardAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(OptoSession, OptoSessionAdmin)
admin.site.register(GrandSession, GrandSessionAdmin)
admin.site.register(BehaviorCage)
admin.site.register(ArduinoProtocol)
admin.site.register(PythonProtocol)