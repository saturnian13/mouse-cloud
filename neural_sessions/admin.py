from django.contrib import admin
import neural_sessions.models



class NeuralSessionInline(admin.StackedInline):
    """For a tab within GrandSession"""
    model = neural_sessions.models.NeuralSession
    fields = (
        'name', 'sort_name',
    )
    
    suit_classes = 'suit-tab suit-tab-neural'

# Register your models here.
class NeuralSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'sort_name', 'bsession',]

admin.site.register(neural_sessions.models.NeuralSession, NeuralSessionAdmin)
