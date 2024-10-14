from django.contrib import admin

from .models import *

class ResourceAdmin(admin.ModelAdmin):
    list_display = ("resource",)
admin.site.register(Resource, ResourceAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ("resource", "tag")
    list_filter = ("resource",)
admin.site.register(Tag, TagAdmin)
