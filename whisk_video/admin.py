from django.contrib import admin
import whisk_video.models

# Register your models here.
class VideoSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'bsession',]

admin.site.register(whisk_video.models.VideoSession, VideoSessionAdmin)
