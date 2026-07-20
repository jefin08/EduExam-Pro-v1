from django.db import models
from django.conf import settings
from content.models import Topic
from accounts.models import Class

class Exam(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exams')
    topics = models.ManyToManyField(Topic, related_name='exams', help_text="Topics this exam draws questions from")
    name = models.CharField(max_length=200)
    duration_minutes = models.IntegerField(help_text="Duration of the exam in minutes")
    start_time = models.DateTimeField(help_text="Start of the scheduled window")
    end_time = models.DateTimeField(help_text="End of the scheduled window")
    is_randomized = models.BooleanField(default=False, help_text="Randomize question ordering for each student")
    allowed_attempts = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ExamCode(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='codes')
    code = models.CharField(max_length=50, unique=True, help_text="Unique exam access code")
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='exam_codes', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} -> {self.exam.name}"

class OfficialGrade(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='official_grades')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='grades')
    score = models.FloatField(default=0.0)
    mcq_score = models.FloatField(default=0.0)
    coding_score = models.FloatField(default=0.0)
    is_submitted = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student.username} - {self.exam.name}: {self.score}"

class MonitoringEvent(models.Model):
    EVENT_TYPES = (
        ('tab_switch', 'Tab Switch'),
        ('copy_paste', 'Copy Paste'),
        ('blur', 'Focus Lost'),
    )
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monitoring_events')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='monitoring_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.event_type} at {self.timestamp}"
