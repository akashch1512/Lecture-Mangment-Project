from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='is_teacher')
def is_teacher(user):
    """
    Template filter to check if a user is in the teacher group
    Usage: {% if user|is_teacher %}
    """
    return user.groups.filter(name='Teacher').exists()

@register.filter(name='is_student')
def is_student(user):
    """
    Template filter to check if a user is in the student group
    Usage: {% if user|is_student %}
    """
    return user.groups.filter(name='Student').exists()