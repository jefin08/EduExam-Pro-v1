from django.urls import path
from .views import (
    signup_selection_view, teacher_signup_view, student_signup_view, signin_view, signout_view,
    admin_dashboard_view, teacher_dashboard_view, student_dashboard_view,
    teacher_exams_view, teacher_practice_view, teacher_exams_questions_view, teacher_practice_questions_view, teacher_create_practice_page_view, teacher_schedule_exam_view,
    admin_create_class, admin_create_teacher, admin_create_student, admin_approve_teacher, admin_approve_student,
    teacher_create_topic, teacher_edit_topic, teacher_create_mcq, teacher_create_coding,
    teacher_create_practice, teacher_create_exam, student_join_exam, teacher_toggle_visibility,
    teacher_edit_exam_schedule, teacher_topic_questions,
    teacher_delete_mcq, teacher_delete_coding, teacher_edit_mcq, teacher_edit_coding,
    teacher_bulk_upload_view, teacher_bulk_save_view
)

urlpatterns = [
    # Auth
    path('signup/', signup_selection_view, name='signup_selection'),
    path('signup/teacher/', teacher_signup_view, name='signup'),
    path('signup/student/', student_signup_view, name='signup_student'),
    path('signin/', signin_view, name='signin'),
    path('signout/', signout_view, name='signout'),
    
    # Dashboards
    path('dashboard/admin/', admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/teacher/', teacher_dashboard_view, name='teacher_dashboard'),
    path('dashboard/teacher/exams/', teacher_exams_view, name='teacher_exams'),
    path('dashboard/teacher/exams/schedule/', teacher_schedule_exam_view, name='teacher_schedule_exam'),
    path('dashboard/teacher/exams/questions/', teacher_exams_questions_view, name='teacher_exams_questions'),
    path('dashboard/teacher/practice/', teacher_practice_view, name='teacher_practice'),
    path('dashboard/teacher/practice/new/', teacher_create_practice_page_view, name='teacher_create_practice_page'),
    path('dashboard/teacher/practice/questions/', teacher_practice_questions_view, name='teacher_practice_questions'),
    path('dashboard/teacher/practice/questions/bulk/', teacher_bulk_upload_view, name='teacher_bulk_upload'),
    path('dashboard/teacher/practice/questions/bulk/save/', teacher_bulk_save_view, name='teacher_bulk_save'),
    path('dashboard/student/', student_dashboard_view, name='student_dashboard'),
    
    # Admin Actions
    path('dashboard/admin/class/create/', admin_create_class, name='admin_create_class'),
    path('dashboard/admin/teacher/create/', admin_create_teacher, name='admin_create_teacher'),
    path('dashboard/admin/teacher/<int:teacher_id>/approve/', admin_approve_teacher, name='admin_approve_teacher'),
    path('dashboard/admin/student/create/', admin_create_student, name='admin_create_student'),
    path('dashboard/admin/student/<int:student_id>/approve/', admin_approve_student, name='admin_approve_student'),
    
    # Teacher Actions
    path('dashboard/teacher/topic/create/', teacher_create_topic, name='teacher_create_topic'),
    path('dashboard/teacher/topic/<int:topic_id>/edit/', teacher_edit_topic, name='teacher_edit_topic'),
    path('dashboard/teacher/topic/<int:topic_id>/questions/', teacher_topic_questions, name='teacher_topic_questions'),
    path('dashboard/teacher/topic/<int:topic_id>/toggle-visibility/<int:class_id>/', teacher_toggle_visibility, name='teacher_toggle_visibility'),
    path('dashboard/teacher/question/mcq/create/', teacher_create_mcq, name='teacher_create_mcq'),
    path('dashboard/teacher/question/mcq/<int:question_id>/edit/', teacher_edit_mcq, name='teacher_edit_mcq'),
    path('dashboard/teacher/question/mcq/<int:question_id>/delete/', teacher_delete_mcq, name='teacher_delete_mcq'),
    path('dashboard/teacher/question/coding/create/', teacher_create_coding, name='teacher_create_coding'),
    path('dashboard/teacher/question/coding/<int:question_id>/edit/', teacher_edit_coding, name='teacher_edit_coding'),
    path('dashboard/teacher/question/coding/<int:question_id>/delete/', teacher_delete_coding, name='teacher_delete_coding'),
    path('dashboard/teacher/practice/create/', teacher_create_practice, name='teacher_create_practice'),
    path('dashboard/teacher/exam/create/', teacher_create_exam, name='teacher_create_exam'),
    path('dashboard/teacher/exam/<int:exam_id>/edit-schedule/', teacher_edit_exam_schedule, name='teacher_edit_exam_schedule'),
    
    # Student Actions
    path('dashboard/student/exam/join/', student_join_exam, name='student_join_exam'),
]
