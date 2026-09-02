from django.urls import path
from .views import (
    signup_selection_view, teacher_signup_view, student_signup_view, signin_view, signout_view,
    admin_dashboard_view, teacher_dashboard_view, student_dashboard_view,
    teacher_exams_view, teacher_practice_view,
    admin_create_class, admin_create_teacher, admin_create_student, admin_approve_teacher, admin_approve_student, admin_pending_count_api, admin_create_department,
    teacher_create_topic, teacher_edit_topic, teacher_create_mcq, teacher_create_coding,
    teacher_create_practice, teacher_create_exam, student_join_exam, teacher_toggle_visibility, teacher_practice_toggle_visibility,
    teacher_edit_exam_schedule, teacher_toggle_exam_code_visibility,
    teacher_delete_mcq, teacher_delete_coding, teacher_edit_mcq, teacher_edit_coding,
    teacher_bulk_upload_view, teacher_bulk_save_view, teacher_import_practice_to_exam,
    student_profile_view, student_scheduled_exams_view, student_practice_sets_view, student_assessment_history_view,
    teacher_profile_view
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
    path('dashboard/teacher/profile/', teacher_profile_view, name='teacher_profile'),
    path('dashboard/teacher/exams/', teacher_exams_view, name='teacher_exams'),
    path('dashboard/teacher/exams/code/<int:exam_code_id>/toggle/', teacher_toggle_exam_code_visibility, name='teacher_toggle_exam_code_visibility'),
    path('dashboard/teacher/practice/', teacher_practice_view, name='teacher_practice'),
    path('dashboard/teacher/practice/questions/bulk/', teacher_bulk_upload_view, name='teacher_bulk_upload'),
    path('dashboard/teacher/practice/questions/bulk/save/', teacher_bulk_save_view, name='teacher_bulk_save'),
    path('dashboard/student/', student_dashboard_view, name='student_dashboard'),
    path('dashboard/student/profile/', student_profile_view, name='student_profile'),
    
    # Admin Actions
    path('dashboard/admin/class/create/', admin_create_class, name='admin_create_class'),
    path('dashboard/admin/teacher/create/', admin_create_teacher, name='admin_create_teacher'),
    path('dashboard/admin/teacher/<int:teacher_id>/approve/', admin_approve_teacher, name='admin_approve_teacher'),
    path('dashboard/admin/student/create/', admin_create_student, name='admin_create_student'),
    path('dashboard/admin/student/<int:student_id>/approve/', admin_approve_student, name='admin_approve_student'),
    path('dashboard/admin/department/create/', admin_create_department, name='admin_create_department'),
    path('dashboard/admin/pending-count/', admin_pending_count_api, name='admin_pending_count'),
    
    # Teacher Actions
    path('dashboard/teacher/topic/create/', teacher_create_topic, name='teacher_create_topic'),
    path('dashboard/teacher/topic/<int:topic_id>/edit/', teacher_edit_topic, name='teacher_edit_topic'),
    path('dashboard/teacher/topic/<int:topic_id>/import/', teacher_import_practice_to_exam, name='teacher_import_practice_to_exam'),
    path('dashboard/teacher/topic/<int:topic_id>/toggle-visibility/<int:class_id>/', teacher_toggle_visibility, name='teacher_toggle_visibility'),
    path('dashboard/teacher/practice/<int:practice_set_id>/toggle-visibility/<int:class_id>/', teacher_practice_toggle_visibility, name='teacher_practice_toggle_visibility'),
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
    path('dashboard/student/scheduled-exams/', student_scheduled_exams_view, name='student_scheduled_exams'),
    path('dashboard/student/practice-sets/', student_practice_sets_view, name='student_practice_sets'),
    path('dashboard/student/assessment-history/', student_assessment_history_view, name='student_assessment_history'),
    path('dashboard/student/exam/join/', student_join_exam, name='student_join_exam'),
]
