from django.contrib import admin
from .models import Topic, TopicClassVisibility, MCQQuestion, CodingQuestion

admin.site.register(Topic)
admin.site.register(TopicClassVisibility)
admin.site.register(MCQQuestion)
admin.site.register(CodingQuestion)
