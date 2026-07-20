from django.contrib import admin
from .models import Submission, TestCaseResult

admin.site.register(Submission)
admin.site.register(TestCaseResult)
