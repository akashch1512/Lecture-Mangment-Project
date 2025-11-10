

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

ROLE_CHOICES = (('teacher','Teacher'), ('student','Student'))
PROGRESS_STATUS_CHOICES = (
    ('not_started', 'Not Started'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed')
)

class Subject(models.Model):
    """A subject in a class (e.g., Cyber Security) with planned lectures + schedule window."""
    name = models.CharField(max_length=200, unique=True)
    class_name = models.CharField(max_length=120, default="CSE-SEM-1")
    planned_lectures = models.PositiveIntegerField(default=24)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_subjects', null=True)

    def __str__(self):
        return f"{self.class_name} · {self.name}"

    @property
    def conducted_lectures(self):
        return self.sessions.count()

    @property
    def remaining_lectures(self):
        return max(self.planned_lectures - self.conducted_lectures, 0)

    @property
    def progress_percent(self):
        """Calculate overall progress percentage across all students."""
        total_topics = Topic.objects.filter(chapter__subject=self).count()
        if total_topics == 0:
            return 0
        
        completed = TopicProgress.objects.filter(
            topic__chapter__subject=self,
            status='completed'
        ).count()
        in_progress = TopicProgress.objects.filter(
            topic__chapter__subject=self,
            status='in_progress'
        ).count()
        
        student_count = User.objects.filter(groups__name='Student').count()
        if student_count == 0:
            return 0
            
        # Count completed as 100% and in_progress as 50%
        weighted_progress = (completed + (in_progress * 0.5)) / student_count
        return round((weighted_progress / total_topics) * 100, 1)

class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('order', 'id')

    def __str__(self):
        return f"{self.subject.name}: {self.title}"

class Topic(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=250)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('order', 'id')
        unique_together = ('chapter','title')

    def __str__(self):
        return self.title

class TopicStatus(models.Model):
    """Completion status at class/subject level (teacher updates, students view)."""
    topic = models.OneToOneField(Topic, on_delete=models.CASCADE, related_name='status')
    completed = models.BooleanField(default=False)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.topic} - {'Done' if self.completed else 'Pending'}"

class LectureSession(models.Model):
    """Attendance & lecture count tracking."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField(default=timezone.now)
    attendees = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ('-date','-id')

    def __str__(self):
        return f"{self.subject.name} · {self.date} · {self.attendees}"

class Enrollment(models.Model):
    """Student enrollment to subjects."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    class Meta:
        unique_together = ('user','subject','role')

    def __str__(self):
        return f"{self.user.username} → {self.subject.name} ({self.role})"


class TopicProgress(models.Model):
    """Tracks a student's progress on individual topics."""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topic_progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='student_progress')
    status = models.CharField(max_length=20, choices=PROGRESS_STATUS_CHOICES, default='not_started')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'topic']
        ordering = ['topic__chapter__order', 'topic__order']

    def __str__(self):
        return f"{self.student.username} - {self.topic.title}: {self.get_status_display()}"

class Profile(models.Model):
    """Extended user profile to store optional user details used in the UI."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    # optional avatar field could be added later (ImageField) with media settings

    def __str__(self):
        return f"Profile: {self.user.username}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Ensure a Profile exists for every User."""
    if created:
        Profile.objects.create(user=instance)
    else:
        # in case code elsewhere updated user, ensure profile exists
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)
