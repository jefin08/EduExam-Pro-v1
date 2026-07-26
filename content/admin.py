from django.contrib import admin
from .models import Topic, TopicClassVisibility, PracticeMCQQuestion, PracticeCodingQuestion, ExamMCQQuestion, ExamCodingQuestion

admin.site.register(Topic)
admin.site.register(TopicClassVisibility)
admin.site.register(PracticeMCQQuestion)
admin.site.register(PracticeCodingQuestion)
admin.site.register(ExamMCQQuestion)
admin.site.register(ExamCodingQuestion)
