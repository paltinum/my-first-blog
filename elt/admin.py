from django.contrib import admin
from django.contrib.auth.models import Group
from .models import ELTcores, Snippet, Post, Comment
# Register your models here.

admin.site.site_header = 'Platinum Admin Dashboard'
admin.site.site_title = "Platinum Admin Dashboard"
admin.site.register(ELTcores)
admin.site.register(Snippet)
admin.site.register(Post)
admin.site.register(Comment)