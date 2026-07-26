from django.db import models
from django.conf import settings
from content.models import Topic
from accounts.models import Class

class PracticeSet(models.Model):
    REVEAL_RULES = (
        ('immediate', 'After First Attempt'),
        ('never', 'Never'),
    )
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='practice_sets')
    topics = models.ManyToManyField(Topic, related_name='practice_sets', help_text="Topics this practice set is built from")
    name = models.CharField(max_length=200)
    solution_reveal_rule = models.CharField(max_length=20, choices=REVEAL_RULES, default='immediate')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class PracticeSetClassAssignment(models.Model):
    practice_set = models.ForeignKey(PracticeSet, on_delete=models.CASCADE, related_name='assignments')
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='practice_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('practice_set', 'class_group')
        verbose_name_plural = "Practice Set Class Assignments"

    def __str__(self):
        return f"{self.practice_set.name} assigned to {self.class_group.name}"

class PracticeAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='practice_attempts')
    practice_set = models.ForeignKey(PracticeSet, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(default=0.0)
    mcq_score = models.FloatField(default=0.0)
    coding_score = models.FloatField(default=0.0)
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.practice_set.name}: {self.score} at {self.attempted_at}"

class PracticeComment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='practice_comments')
    question_type = models.CharField(max_length=10, choices=(('mcq', 'MCQ'), ('coding', 'Coding')))
    mcq_question = models.ForeignKey('content.PracticeMCQQuestion', on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    coding_question = models.ForeignKey('content.PracticeCodingQuestion', on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.student.username} on {self.question_type} {self.id}"
