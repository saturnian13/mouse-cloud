from django.contrib import admin
import whiskvid.models

# Register your models here.
class VideoSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'bsession',]

admin.site.register(whiskvid.models.VideoSession, VideoSessionAdmin)
