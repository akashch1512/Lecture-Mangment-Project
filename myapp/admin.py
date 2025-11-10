from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Subject, Chapter, Topic, TopicStatus, LectureSession, Enrollment

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name','class_name','planned_lectures','start_date','end_date')
    search_fields = ('name','class_name')

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title','subject','order')
    list_filter = ('subject',)
    ordering = ('subject','order')

class TopicStatusInline(admin.StackedInline):
    model = TopicStatus
    extra = 0

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title','chapter','order')
    list_filter = ('chapter__subject','chapter')
    inlines = [TopicStatusInline]
    ordering = ('chapter','order')

@admin.register(LectureSession)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('subject','date','attendees','notes')
    list_filter = ('subject',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user','subject','role')
    list_filter = ('role','subject')
    search_fields = ('user__username',)
