from django.contrib import admin
import neural_sessions.models

# Register your models here.
class NeuralSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'sort_name', 'bsession',]

admin.site.register(neural_sessions.models.NeuralSession, NeuralSessionAdmin)
