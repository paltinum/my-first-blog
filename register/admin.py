from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Profile, Student
from import_export.admin import ImportExportModelAdmin

# Register your models here.

admin.site.site_header = 'Platinum Admin Dashboard'
admin.site.site_title = "Platinum Admin Dashboard"
admin.site.register(Profile)


@admin.register(Student)
class ProfileAdmin(ImportExportModelAdmin):
	pass