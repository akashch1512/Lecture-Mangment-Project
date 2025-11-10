from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', LogoutView.as_view(), name='logout'),


    # dashboards
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),

    # auth / accounts
    path('signup/', views.signup_view, name='signup'),
    path('login/<str:role>/', views.login_role, name='login_role'),
    path('profile/', views.profile_view, name='profile'),
    path('teacher/profile/<int:pk>/', views.teacher_profile_view, name='teacher_profile'),

    # subject detail + partials
    path('subject/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('subject/<int:pk>/progress/', views.progress_partial, name='progress_partial'),  # HTMX poll
    
    # chapter management
    path('subject/<int:pk>/chapter/add/', views.add_chapter, name='add_chapter'),
    path('chapter/<int:pk>/edit/', views.edit_chapter, name='edit_chapter'),
    path('chapter/<int:pk>/delete/', views.delete_chapter, name='delete_chapter'),
    
    # topic management
    path('chapter/<int:pk>/topic/add/', views.add_topic, name='add_topic'),
    path('topic/<int:topic_id>/toggle/', views.toggle_topic, name='toggle_topic'),

    # topic toggle (HTMX)
    path('topic/<int:topic_id>/toggle/', views.toggle_topic, name='toggle_topic'),

    # attendance
    path('subject/<int:pk>/session/add/', views.add_session, name='add_session'),

    # printable reports
    path('report/subject/<int:pk>/', views.subject_report, name='subject_report'),
]
