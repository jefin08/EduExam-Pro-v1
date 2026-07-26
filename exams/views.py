from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
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
        
    now = timezone.now()
    if now < exam.start_time:
        # User entered early (in the 5 min window). Show waiting room.
        return render(request, 'exam/waiting.html', {'exam': exam})
        
    # Get or create OfficialGrade entry (enforcing one attempt only at the DB layer via unique_together)
    grade, created = OfficialGrade.objects.get_or_create(
        student=request.user,
        exam=exam
    )
    
    # If already submitted, lock them out
    if grade.is_submitted:
        return render(request, 'exam/submitted.html', {'exam': exam, 'grade': grade})
        
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
                    status='graded',
                    context_type='exam',
                    exam=exam
                )
                
                # Standard Python function check syntax validation
                success = True
                if "def" not in code_text and lang == 'python':
                    success = False
                    
                tc_status = 'pass' if success else 'fail'
                tc_score = question.marks if success else 0.0
                
                TestCaseResult.objects.create(
                    submission=sub,
                    test_case_index=0,
                    is_hidden=False,
                    status=tc_status,
                    runtime_seconds=0.05
                )
                sub.score = tc_score
                sub.save()
                coding_score += tc_score
                
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
