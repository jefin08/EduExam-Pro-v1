from django.db import models
from django.conf import settings

class Topic(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics')
    subject = models.CharField(max_length=120)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.subject})"

    @property
    def visible_class_ids(self):
        return list(self.visibilities.values_list('class_group_id', flat=True))

class TopicClassVisibility(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='visibilities')
    class_group = models.ForeignKey('accounts.Class', on_delete=models.CASCADE, related_name='visible_topics')

    class Meta:
        unique_together = ('topic', 'class_group')
        verbose_name_plural = "Topic Class Visibilities"

    def __str__(self):
        return f"{self.topic.name} visible to {self.class_group.name}"

class MCQQuestion(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='mcq_questions')
    question_text = models.TextField()
    options = models.JSONField(help_text="A list of option strings")
    correct_option_index = models.IntegerField(help_text="0-indexed index of correct option")
    explanation = models.TextField(blank=True, null=True)
    marks = models.IntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    tags = models.JSONField(default=list, blank=True, help_text="A list of tags")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MCQ: {self.question_text[:50]}..."

class CodingQuestion(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='coding_questions')
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
        return f"Code: {self.title}"
