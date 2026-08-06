"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from practice.views import attempt_practice_set_view, publish_comment_view
from exams.views import take_exam_view, teacher_monitor_view, log_monitoring_event
from judge.views import run_custom_code_view, run_sample_tests_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    path('', include('accounts.urls')),
    path('practice/<int:set_id>/', attempt_practice_set_view, name='attempt_practice'),
    path('practice/comment/publish/', publish_comment_view, name='publish_comment'),
    path('exam/<int:exam_id>/', take_exam_view, name='take_exam'),
    path('exam/<int:exam_id>/monitor/', teacher_monitor_view, name='teacher_monitor'),
    path('exam/<int:exam_id>/event/', log_monitoring_event, name='log_monitoring_event'),
    path('judge/run-custom/', run_custom_code_view, name='run_custom_code'),
    path('judge/run-samples/', run_sample_tests_view, name='run_sample_tests'),
]

if settings.DEBUG:
    # Ensure static files are accessible in debug/local development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
