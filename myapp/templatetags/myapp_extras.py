from django import template
from myapp.views import _is_teacher, _is_student

register = template.Library()

@register.filter
def is_teacher(user):
    return _is_teacher(user)

@register.filter
def is_student(user):
    return _is_student(user)