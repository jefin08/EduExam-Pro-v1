from django.db import models
from django.conf import settings

class Topic(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics')
    subject = models.CharField(max_length=120)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    purpose = models.CharField(
        max_length=20, 
        choices=[('exam', 'Exam'), ('practice', 'Practice'), ('both', 'Both')], 
        default='both'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.subject})"

    @property
    def visible_class_ids(self):
        return list(self.visibilities.values_list('class_group_id', flat=True))

    @property
    def exam_questions_count(self):
        return self.exam_mcq_questions.count() + self.exam_coding_questions.count()

    @property
    def practice_questions_count(self):
        return self.practice_mcq_questions.count() + self.practice_coding_questions.count()

class TopicClassVisibility(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='visibilities')
    class_group = models.ForeignKey('accounts.Class', on_delete=models.CASCADE, related_name='visible_topics')

    class Meta:
        unique_together = ('topic', 'class_group')
        verbose_name_plural = "Topic Class Visibilities"

    def __str__(self):
        return f"{self.topic.name} visible to {self.class_group.name}"

class PracticeMCQQuestion(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='practice_mcq_questions')
    question_text = models.TextField()
    options = models.JSONField(help_text="A list of option strings")
    correct_option_index = models.IntegerField(help_text="0-indexed index of correct option")
    explanation = models.TextField(blank=True, null=True)
    marks = models.IntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    tags = models.JSONField(default=list, blank=True, help_text="A list of tags")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Practice MCQ: {self.question_text[:50]}..."

class ExamMCQQuestion(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='exam_mcq_questions')
    question_text = models.TextField()
    options = models.JSONField(help_text="A list of option strings")
    correct_option_index = models.IntegerField(help_text="0-indexed index of correct option")
    explanation = models.TextField(blank=True, null=True)
    marks = models.IntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    tags = models.JSONField(default=list, blank=True, help_text="A list of tags")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Exam MCQ: {self.question_text[:50]}..."

class PracticeCodingQuestion(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='practice_coding_questions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    input_format = models.TextField()
    output_format = models.TextField()
    sample_test_cases = models.JSONField(help_text="List of dicts with 'input' and 'output'")
    hidden_test_cases = models.JSONField(help_text="List of dicts with 'input' and 'output'")
    starter_code = models.TextField(blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)
    time_limit = models.FloatField(default=1.0, help_text="Time limit in seconds")
    memory_limit = models.IntegerField(default=256, help_text="Memory limit in MB")
    marks = models.IntegerField(default=5)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    tags = models.JSONField(default=list, blank=True, help_text="A list of tags")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Practice Code: {self.title}"

class ExamCodingQuestion(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='exam_coding_questions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    input_format = models.TextField()
    output_format = models.TextField()
    sample_test_cases = models.JSONField(help_text="List of dicts with 'input' and 'output'")
    hidden_test_cases = models.JSONField(help_text="List of dicts with 'input' and 'output'")
    starter_code = models.TextField(blank=True, null=True)
    time_limit = models.FloatField(default=1.0, help_text="Time limit in seconds")
    memory_limit = models.IntegerField(default=256, help_text="Memory limit in MB")
    marks = models.IntegerField(default=5)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    tags = models.JSONField(default=list, blank=True, help_text="A list of tags")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Exam Code: {self.title}"
