import numpy as np
import pandas
from django.contrib import admin
import whisk_video.models

from django.forms import TextInput, Textarea
from django.db import models

## Filtering by tagging
# https://djangosnippets.org/snippets/2807/
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from taggit.models import TaggedItem 

from runner.models import GrandSession

class TaggitListFilter(SimpleListFilter):
    """
    A custom filter class that can be used to filter by taggit tags in the admin.
    
    Edited to work for the grand_session OneToOneField
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
        
        # Instead of model_admin (VideoSession), always search for GrandSession
        tags = TaggedItem.tags_for(GrandSession)
        for tag in tags:
            list.append( (tag.name, _(tag.name)) )
        return list    

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value provided in the query
        string and retrievable via `self.value()`.
        """
        if self.value():
            # Search on linked grand_session
            return queryset.filter(grand_session__tags__name__in=[self.value()])

class VideoSessionInline(admin.StackedInline):
    """For a tab within GrandSession"""
    model = whisk_video.models.VideoSession
    fields = (
        'name', 'frame_height', 'frame_width', 'frame_rate',
        'lens_fstop', 'imaq_exposure_time', 'imaq_digital_gain',
        'imaq_digital_offset', 'notes', 'whisker_colors', 'hide',
    )
    
    suit_classes = 'suit-tab suit-tab-video'

class VideoSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'tags', 'bsession', 
        'whiskers_isnotnull', 'sync_isnotnull',
        'edges_isnotnull', 'tac_isnotnull',
        'clustered_tac_isnotnull', 'cs_isnotnull', 
        'colorized_isnotnull', 'ccs_isnotnull',
        'notes',
    ]
    
    list_filter = [
        TaggitListFilter,
    ]
    
    # Make the "notes" field a wider editable box
    list_editable = ['notes',]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={
            'rows':2, 'cols':80, 'style': 'width: 45em;resize: vertical;'})},
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
    
    def tags(self, obj):
        return ", ".join([o.name for o in obj.grand_session.tags.all()])


admin.site.register(whisk_video.models.VideoSession, VideoSessionAdmin)
