from django.contrib import admin
from .models import Mouse, Box, Board, ArduinoProtocol, \
    PythonProtocol, Session, BehaviorCage
from suit.admin import SortableModelAdmin

# Register your models here.

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

class SessionAdmin(admin.ModelAdmin):
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
        'husbandry_name', 'name', 'in_training', 'training_cohort', 
        'dob', 'notes', 'sack_date', 'genotype', 'headplate_color', 'cage',
    ]
    
    list_editable = ['in_training', 'training_cohort']

class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ['date_time_start']
    inlines = [SessionInline]

admin.site.register(Mouse, MouseAdmin)
admin.site.register(Box, BoxAdmin)
admin.site.register(Board, BoardAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(BehaviorCage)
admin.site.register(ArduinoProtocol)
admin.site.register(PythonProtocol)