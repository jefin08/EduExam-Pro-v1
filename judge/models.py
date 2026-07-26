from django.db import models
from django.conf import settings
from content.models import PracticeCodingQuestion, ExamCodingQuestion
from exams.models import Exam
from practice.models import PracticeSet

class Submission(models.Model):
    LANGUAGES = (
        ('python', 'Python'),
        ('cpp', 'C++'),
        ('java', 'Java'),
    )
    STATUSES = (
        ('queued', 'Queued'),
        ('judging', 'Judging'),
        ('compile_error', 'Compilation Error'),
        ('graded', 'Graded'),
    )
    CONTEXTS = (
        ('exam', 'Exam'),
        ('practice', 'Practice'),
        ('standalone', 'Standalone'),
    )

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    practice_coding_question = models.ForeignKey(PracticeCodingQuestion, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    exam_coding_question = models.ForeignKey(ExamCodingQuestion, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    code = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGES, default='python')
    status = models.CharField(max_length=20, choices=STATUSES, default='queued')
    score = models.FloatField(default=0.0, help_text="Total marks/score received")
    compile_output = models.TextField(blank=True, null=True, help_text="Compiler or Interpreter output logs")
    context_type = models.CharField(max_length=20, choices=CONTEXTS, default='standalone')
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    practice_set = models.ForeignKey(PracticeSet, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)

    @property
    def question(self):
        return self.practice_coding_question or self.exam_coding_question

    def __str__(self):
        q_title = self.question.title if self.question else "Unknown"
        return f"Submission {self.id} - User: {self.student.username} - Question: {q_title}"

class TestCaseResult(models.Model):
    STATUS_CHOICES = (
        ('pass', 'Pass'),
        ('fail', 'Wrong Answer'),
        ('runtime_error', 'Runtime Error'),
        ('time_limit_exceeded', 'Time Limit Exceeded'),
        ('memory_limit_exceeded', 'Memory Limit Exceeded'),
    )
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='testcase_results')
    test_case_index = models.IntegerField(help_text="0-indexed position of the testcase in lists")
    is_hidden = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    runtime_seconds = models.FloatField(default=0.0)
    memory_bytes = models.IntegerField(default=0)
    output_received = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Result {self.id} for Submission {self.submission_id} (TC {self.test_case_index}): {self.status}"
