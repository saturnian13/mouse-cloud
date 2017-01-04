import numpy as np
import pandas
from django.contrib import admin
import whisk_video.models

from django.forms import TextInput, Textarea
from django.db import models

# Register your models here.
class VideoSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'bsession', 
        'whiskers_isnotnull', 'sync_isnotnull',
        'edges_isnotnull', 'tac_isnotnull',
        'clustered_tac_isnotnull', 'cs_isnotnull', 
        'colorized_isnotnull', 'ccs_isnotnull',
        'notes',
    ]
    
    list_filter = ['hide',]
    
    # Make the "notes" field a wider editable box
    list_editable = ['notes',]
    formfield_overrides = {
        models.CharField: {'widget': Textarea(attrs={
            'rows':1, 'cols':80, 'style': 'width: 45em;resize: vertical;'})},
    }
    
    def whiskers_isnotnull(self, obj):
        val = obj.whiskers_table_filename
        return val is not None and val != ''
    whiskers_isnotnull.short_description = 'whiskers'
    whiskers_isnotnull.boolean = True

    def edges_isnotnull(self, obj):
        val = obj.all_edges_filename
        return val is not None and val != ''
    edges_isnotnull.short_description = 'edges'
    edges_isnotnull.boolean = True

    def tac_isnotnull(self, obj):
        val = obj.tac_filename
        return val is not None and val != ''
    tac_isnotnull.short_description = 'tac'
    tac_isnotnull.boolean = True

    def clustered_tac_isnotnull(self, obj):
        val = obj.clustered_tac_filename
        return val is not None and val != ''
    clustered_tac_isnotnull.short_description = 'clustered'
    clustered_tac_isnotnull.boolean = True

    def colorized_isnotnull(self, obj):
        val = obj.colorized_whisker_ends_filename
        return val is not None and val != ''
    colorized_isnotnull.short_description = 'colorized'
    colorized_isnotnull.boolean = True

    def cs_isnotnull(self, obj):
        val = obj.contacts_summary_filename
        return val is not None and val != ''
    cs_isnotnull.short_description = 'cs'
    cs_isnotnull.boolean = True
    
    def ccs_isnotnull(self, obj):
        val = obj.colorized_contacts_summary_filename
        return val is not None and val != ''
    ccs_isnotnull.short_description = 'ccs'
    ccs_isnotnull.boolean = True
    
    def sync_isnotnull(self, obj):
        return not np.any(pandas.isnull([
            obj.fit_v2b0, obj.fit_v2b1, obj.fit_b2v0, obj.fit_b2v1]))

    sync_isnotnull.short_description = 'sync'
    sync_isnotnull.boolean = True        

admin.site.register(whisk_video.models.VideoSession, VideoSessionAdmin)
