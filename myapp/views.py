from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.db.models import Count
from .models import Subject, Chapter, Topic, TopicStatus, LectureSession, Enrollment, TopicProgress
from .forms import SignupForm, ProfileForm, ProfileExtendedForm

def _is_teacher(user):
    return user.is_staff or user.groups.filter(name__iexact='Teacher').exists()

def _is_student(user):
    return user.groups.filter(name__iexact='Student').exists()


def login_role(request, role=None):
    """Role-aware login: only allow users of given role to login via that path."""
    from django.contrib.auth.forms import AuthenticationForm
    role = (role or '').lower()
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # validate role
            is_teacher = _is_teacher(user)
            is_student = _is_student(user)
            if role == 'teacher' and not is_teacher:
                messages.error(request, 'This login is for teachers only.')
            elif role == 'student' and not is_student:
                messages.error(request, 'This login is for students only.')
            else:
                auth_login(request, user)
                return redirect('teacher_dashboard' if is_teacher else 'student_dashboard')
    else:
        form = __import__('django.contrib.auth.forms', fromlist=['']).AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form, 'role': role})


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # auto-login
            auth_user = authenticate(request, username=user.username, password=request.POST.get('password1'))
            if auth_user:
                auth_login(request, auth_user)
            messages.success(request, 'Account created and logged in')
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'myapp/signup.html', {'form': form})


@login_required
def profile_view(request):
    # show and edit the current user's profile
    if request.method == 'POST':
        form_user = ProfileForm(request.POST, instance=request.user)
        form_ext = ProfileExtendedForm(request.POST, instance=request.user.profile)
        if form_user.is_valid() and form_ext.is_valid():
            form_user.save()
            form_ext.save()
            messages.success(request, 'Profile updated')
            return redirect('profile')
    else:
        form_user = ProfileForm(instance=request.user)
        form_ext = ProfileExtendedForm(instance=request.user.profile)
    # role label
    role_label = 'Teacher' if _is_teacher(request.user) else 'Student' if _is_student(request.user) else 'User'
    return render(request, 'myapp/profile.html', {'form_user': form_user, 'form_ext': form_ext, 'role_label': role_label})


@user_passes_test(lambda u: _is_teacher(u))
def teacher_profile_view(request, pk):
    # show details for a teacher user; only accessible by teachers
    teacher = get_object_or_404(User, pk=pk)
    # ensure target is a teacher
    if not _is_teacher(teacher):
        return HttpResponseBadRequest('Not a teacher')
    return render(request, 'myapp/teacher_profile.html', {'teacher': teacher})

@login_required
def home(request):
    return redirect('teacher_dashboard' if _is_teacher(request.user) else 'student_dashboard')

@login_required
@user_passes_test(lambda u: _is_teacher(u))
def teacher_dashboard(request):
    subjects = Subject.objects.filter(teacher=request.user).order_by('class_name','name')  # only teacher's subjects
    alerts = []
    today = timezone.now().date()
    for s in subjects:
        # simple weeks-left heuristic
        weeks_left = max(((s.end_date - today).days // 7) if s.end_date else 12, 1)
        left_pct = 100 - s.progress_percent
        if left_pct > weeks_left * 5:  # arbitrary nudge: >5% per remaining week
            alerts.append(f"{s.name}: {left_pct:.0f}% syllabus left but only ~{weeks_left} weeks remain.")
    return render(request, 'myapp/teacher_dashboard.html', {'subjects': subjects, 'alerts': alerts})

@login_required
def student_dashboard(request):
    subs = Subject.objects.all().order_by('name')
    # If you wire enrollments, filter: subs = Subject.objects.filter(enrollment__user=request.user, enrollment__role='student')
    return render(request, 'myapp/student_dashboard.html', {'subjects': subs})

@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if _is_teacher(request.user) and subject.teacher != request.user:
        messages.error(request, "You don't have permission to view this subject.")
        return redirect('teacher_dashboard')
    chapters = (Chapter.objects.filter(subject=subject)
                .prefetch_related('topics__status'))
    sessions = subject.sessions.all()[:10]
    return render(request, 'myapp/subject_detail.html', {
        'subject': subject, 'chapters': chapters, 'sessions': sessions, 'is_teacher': _is_teacher(request.user)
    })

@login_required
def progress_partial(request, pk):
    """HTMX-polled progress bar."""
    subject = get_object_or_404(Subject, pk=pk)
    if _is_student(request.user):
        # Calculate individual student progress
        total_topics = Topic.objects.filter(chapter__subject=subject).count()
        if total_topics == 0:
            progress_percent = 0
            completed = in_progress = remaining = 0
        else:
            topic_progress = TopicProgress.objects.filter(
                student=request.user,
                topic__chapter__subject=subject
            ).values('status').annotate(count=Count('status'))
            
            progress_counts = {
                'completed': 0,
                'in_progress': 0,
                'not_started': 0
            }
            for p in topic_progress:
                progress_counts[p['status']] = p['count']
                
            completed = progress_counts['completed']
            in_progress = progress_counts['in_progress']
            remaining = progress_counts['not_started']
            
            # Ensure the total of all statuses equals total_topics
            if (completed + in_progress + remaining) < total_topics:
                remaining = total_topics - (completed + in_progress)
                
            progress_percent = (completed + (in_progress * 0.5)) / total_topics * 100 if total_topics > 0 else 0
    else:
        # For teachers, show overall class progress
        total_topics = Topic.objects.filter(chapter__subject=subject).count()
        all_progress = TopicProgress.objects.filter(
            topic__chapter__subject=subject
        ).values('status').annotate(count=Count('status'))
        
        progress_counts = {
            'completed': 0,
            'in_progress': 0,
            'not_started': 0
        }
        for p in all_progress:
            progress_counts[p['status']] = p['count']
            
        student_count = User.objects.filter(groups__name='Student').count()
        if student_count > 0:
            completed = progress_counts['completed'] / student_count
            in_progress = progress_counts['in_progress'] / student_count
            remaining = progress_counts['not_started'] / student_count
            progress_percent = (completed + (in_progress * 0.5)) / total_topics * 100
        else:
            completed = in_progress = remaining = progress_percent = 0
            
    context = {
        'progress_percent': round(progress_percent, 1),
        'completed_topics': round(completed),
        'in_progress_topics': round(in_progress),
        'remaining_topics': round(remaining),
        'subject': subject
    }
    
    return render(request, 'myapp/_progress_bar.html', context)

@login_required
@csrf_protect
def toggle_topic(request, topic_id):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST only")
    
    topic = get_object_or_404(Topic, pk=topic_id)
    
    # Only teachers can toggle topic status
    if not _is_teacher(request.user):
        return HttpResponseBadRequest("Only teachers can mark topics as completed")
    
    # Toggle the topic status (for the whole class)
    st, _ = TopicStatus.objects.get_or_create(topic=topic)
    st.completed = not st.completed
    st.updated_by = request.user
    st.save()
    
    # Update all student progress entries
    student_group = Group.objects.get(name='Student')
    students = User.objects.filter(groups=student_group)
    
    for student in students:
        # Update or create progress entry for each student
        progress, created = TopicProgress.objects.get_or_create(
            student=student,
            topic=topic,
            defaults={'status': 'not_started'}
        )
        # Update the status based on topic completion
        progress.status = 'completed' if st.completed else 'in_progress'
        progress.save()
    st.save()
    
    # Update progress for all students
    student_group = Group.objects.get(name='Student')
    students = User.objects.filter(groups=student_group)
    new_status = 'completed' if st.completed else 'in_progress'
    
    # Bulk update or create progress entries for all students
    for student in students:
        TopicProgress.objects.update_or_create(
            student=student,
            topic=topic,
            defaults={'status': new_status}
        )
    
    # Return the updated row + allow outer page to poll progress bar separately
    return render(request, 'myapp/_topic_row.html', {'t': topic, 'is_teacher': _is_teacher(request.user)})

@login_required
@user_passes_test(lambda u: _is_teacher(u))
def add_session(request, pk):
    """Add a lecture session (attendance + notes)."""
    subject = get_object_or_404(Subject, pk=pk)
    if subject.teacher != request.user:
        messages.error(request, "You don't have permission to add sessions to this subject.")
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        attendees = int(request.POST.get('attendees') or 0)
        notes = request.POST.get('notes','')
        LectureSession.objects.create(subject=subject, attendees=attendees, notes=notes)
        return redirect('subject_detail', pk=pk)
    return HttpResponseBadRequest("POST only")

@login_required
def subject_report(request, pk):
    """Printable HTML that users can save as PDF via browser."""
    
@login_required
@user_passes_test(lambda u: _is_teacher(u))
def add_chapter(request, pk):
    """Add a new chapter to a subject."""
    subject = get_object_or_404(Subject, pk=pk)
    if subject.teacher != request.user:
        messages.error(request, "You don't have permission to modify this subject.")
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            order = Chapter.objects.filter(subject=subject).count() + 1
            chapter = Chapter.objects.create(subject=subject, title=title, order=order)
            return render(request, 'myapp/_chapter_row.html', {'chapter': chapter, 'is_teacher': True})
        return HttpResponseBadRequest("Title is required")
        
    return render(request, 'myapp/_chapter_form.html', {'subject': subject})

@login_required
@user_passes_test(lambda u: _is_teacher(u))
def edit_chapter(request, pk):
    """Edit an existing chapter."""
    chapter = get_object_or_404(Chapter, pk=pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            chapter.title = title
            chapter.save()
            return render(request, 'myapp/_chapter_row.html', {'chapter': chapter, 'is_teacher': True})
        return HttpResponseBadRequest("Title is required")
        
    return render(request, 'myapp/_chapter_form.html', {'chapter': chapter})

@login_required
@user_passes_test(lambda u: _is_teacher(u))
def delete_chapter(request, pk):
    """Delete a chapter and its topics."""
    chapter = get_object_or_404(Chapter, pk=pk)
    if request.method == 'DELETE':
        chapter.delete()
        return HttpResponse(status=204)
    return HttpResponseBadRequest("DELETE method required")

@login_required
@user_passes_test(lambda u: _is_teacher(u))
def add_topic(request, pk):
    """Add a new topic to a chapter."""
    chapter = get_object_or_404(Chapter, pk=pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            order = Topic.objects.filter(chapter=chapter).count() + 1
            topic = Topic.objects.create(chapter=chapter, title=title, order=order)
            return render(request, 'myapp/_topic_row.html', {'t': topic, 'is_teacher': True})
        return HttpResponseBadRequest("Title is required")
        
    return render(request, 'myapp/_topic_form.html', {'chapter': chapter})
    subject = get_object_or_404(Subject, pk=pk)
    chapters = Chapter.objects.filter(subject=subject).prefetch_related('topics__status')
    return render(request, 'myapp/report_subject.html', {'subject': subject, 'chapters': chapters})
