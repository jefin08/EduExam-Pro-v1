from django.contrib import admin
from .models import PracticeSet, PracticeSetClassAssignment, PracticeAttempt, PracticeComment

admin.site.register(PracticeSet)
admin.site.register(PracticeSetClassAssignment)
admin.site.register(PracticeAttempt)
admin.site.register(PracticeComment)
