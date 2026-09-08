from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import Exam, OfficialGrade, MonitoringEvent
from content.models import ExamMCQQuestion, ExamCodingQuestion
from judge.models import Submission, TestCaseResult
import json

@login_required
def take_exam_view(request, exam_id):
    if request.user.role != 'student':
        return redirect('/')
        
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Strictly gate access: student class must have an active code generated for this exam
    if not exam.codes.filter(class_group=request.user.class_group, is_active=True).exists():
        messages.error(request, "Access denied. Your class group is not assigned to this exam.")
        return redirect('/dashboard/student/')
        
    # Get or create OfficialGrade entry (enforcing one attempt only at the DB layer via unique_together)
    # This ensures early joining students show up in the teacher's live monitor status lists
    grade, created = OfficialGrade.objects.get_or_create(
        student=request.user,
        exam=exam
    )
    
    # If already submitted, lock them out
    if grade.is_submitted:
        return render(request, 'exam/submitted.html', {'exam': exam, 'grade': grade})

    now = timezone.now()
    if now < exam.start_time:
        # User entered early. Show waiting room.
        return render(request, 'exam/waiting.html', {'exam': exam})
        
    # Get questions from linked topics
    topics = exam.topics.all()
    mcq_questions = ExamMCQQuestion.objects.filter(topic__in=topics)
    coding_questions = ExamCodingQuestion.objects.filter(topic__in=topics)
    
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        mcq_answers = data.get('mcq_answers', {})
        coding_submissions = data.get('coding_submissions', {})
        
        # 1. Grade MCQs
        mcq_score = 0.0
        for q_id, chosen_idx in mcq_answers.items():
            question = ExamMCQQuestion.objects.filter(id=q_id).first()
            if question and question.correct_option_index == int(chosen_idx):
                mcq_score += question.marks
                
        # 2. Grade Coding
        coding_score = 0.0
        from judge.sandbox import judge_code
        
        for q_id, code_info in coding_submissions.items():
            question = ExamCodingQuestion.objects.filter(id=q_id).first()
            if question:
                code_text = code_info.get('code', '')
                lang = code_info.get('language', 'python')
                
                # Register code submission under exam context
                sub = Submission.objects.create(
                    student=request.user,
                    exam_coding_question=question,
                    code=code_text,
                    language=lang,
                    status='judging',
                    context_type='exam',
                    exam=exam
                )
                
                # Retrieve combined sample and hidden test cases
                test_cases = question.sample_test_cases + question.hidden_test_cases
                
                # Evaluate code via the sandbox
                success, compile_error, results = judge_code(
                    code=code_text,
                    language=lang,
                    test_cases=test_cases,
                    time_limit=getattr(question, 'time_limit', 1.0),
                    memory_limit=getattr(question, 'memory_limit', 256)
                )
                
                if not success:
                    sub.status = 'compile_error'
                    sub.compile_output = compile_error or "Compilation failed."
                    sub.score = 0.0
                    sub.save()
                else:
                    total_passed = 0
                    total_tests = len(results)
                    
                    for res in results:
                        idx = res['test_case_index']
                        is_hidden = idx >= len(question.sample_test_cases)
                        
                        TestCaseResult.objects.create(
                            submission=sub,
                            test_case_index=idx,
                            is_hidden=is_hidden,
                            status=res['status'],
                            runtime_seconds=res['runtime_seconds'],
                            error_message=res['error_message']
                        )
                        if res['status'] == 'pass':
                            total_passed += 1
                            
                    passed_ratio = total_passed / total_tests if total_tests > 0 else 0
                    sub.score = round(question.marks * passed_ratio, 2)
                    sub.status = 'graded'
                    sub.save()
                    coding_score += sub.score
                
        # Update OfficialGrade
        grade.mcq_score = mcq_score
        grade.coding_score = coding_score
        grade.score = mcq_score + coding_score
        grade.is_submitted = True
        grade.submitted_at = timezone.now()
        grade.save()
        
        return JsonResponse({'success': True, 'score': grade.score})
        
    # Calculate exact remaining timer seconds
    elapsed = (timezone.now() - grade.started_at).total_seconds()
    time_limit_secs = exam.duration_minutes * 60
    remaining_seconds = max(0, int(time_limit_secs - elapsed))
    
    context = {
        'exam': exam,
        'mcqs': mcq_questions,
        'coding_qs': coding_questions,
        'remaining_seconds': remaining_seconds,
        'grade': grade,
    }
    return render(request, 'exam/take.html', context)

@login_required
def teacher_monitor_view(request, exam_id):
    if request.user.role != 'teacher':
        return redirect('/')
        
    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)
    grades = OfficialGrade.objects.filter(exam=exam).order_by('-started_at')
    events = MonitoringEvent.objects.filter(exam=exam).order_by('-timestamp')
    
    context = {
        'exam': exam,
        'grades': grades,
        'events': events,
        'now': timezone.now(),
    }
    return render(request, 'exam/monitor.html', context)

@login_required
def log_monitoring_event(request, exam_id):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)
        
    exam = get_object_or_404(Exam, id=exam_id)
    data = json.loads(request.body.decode('utf-8'))
    event_type = data.get('event_type')
    details = data.get('details', '')
    
    if event_type in ['tab_switch', 'copy_paste', 'blur']:
        MonitoringEvent.objects.create(
            student=request.user,
            exam=exam,
            event_type=event_type,
            details=details
        )
        return JsonResponse({'success': True})
        
    return JsonResponse({'success': False}, status=400)

User = get_user_model()

@login_required
def teacher_exam_summary_api(request, exam_id):
    if request.user.role != 'teacher':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)
    now = timezone.now()
    
    # 1. Total Assigned Students
    assigned_classes = exam.codes.filter(is_active=True).values_list('class_group', flat=True)
    assigned_students = User.objects.filter(role='student', class_group__in=assigned_classes).select_related('class_group')
    
    # 2. Grades
    grades = OfficialGrade.objects.filter(exam=exam).select_related('student')
    
    # Lists
    completed_students = []
    completed_late_students = []
    in_progress_students = []
    
    grade_student_ids = set()
    
    for grade in grades:
        grade_student_ids.add(grade.student_id)
        student_data = {
            'id': grade.student.id,
            'name': grade.student.username,
            'entry_time': grade.started_at.strftime('%Y-%m-%d %H:%M:%S'),
            'submit_time': grade.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if grade.submitted_at else 'N/A',
            'score': grade.score,
            'status': 'In Progress' if not grade.is_submitted else 'Completed'
        }
        
        if grade.is_submitted:
            if grade.started_at > exam.start_time and grade.started_at <= exam.start_time + timedelta(minutes=15):
                student_data['scheduled_start'] = exam.start_time.strftime('%Y-%m-%d %H:%M:%S')
                student_data['status'] = 'Completed Late'
                completed_late_students.append(student_data)
            else:
                completed_students.append(student_data)
        else:
            in_progress_students.append(student_data)
            
    # Absent / Not Started
    absent_students = []
    for student in assigned_students:
        if student.id not in grade_student_ids:
            absent_students.append({
                'id': student.id,
                'name': student.username,
                'status': 'Absent' if now > exam.end_time else 'Not Started'
            })
            
    data = {
        'total_students': assigned_students.count(),
        'completed_count': len(completed_students),
        'completed_late_count': len(completed_late_students),
        'in_progress_count': len(in_progress_students),
        'absent_count': len(absent_students),
        'exam_active': now <= exam.end_time,
        
        'completed_students': completed_students,
        'completed_late_students': completed_late_students,
        'in_progress_students': in_progress_students,
        'absent_students': absent_students,
    }
    
    return JsonResponse(data)
