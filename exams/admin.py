from django.contrib import admin
from .models import Exam, ExamCode, OfficialGrade, MonitoringEvent

admin.site.register(Exam)
admin.site.register(ExamCode)
admin.site.register(OfficialGrade)
admin.site.register(MonitoringEvent)
