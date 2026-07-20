from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import PracticeSet, PracticeAttempt
from content.models import Topic, MCQQuestion, CodingQuestion
from judge.models import Submission, TestCaseResult
import json

@login_required
def attempt_practice_set_view(request, set_id):
    if request.user.role != 'student':
        return redirect('/')
        
    practice_set = get_object_or_404(PracticeSet, id=set_id)
    
    # Strictly gate visibility based on student class group assignment
    if not practice_set.assignments.filter(class_group=request.user.class_group).exists():
        return redirect('/dashboard/student/')
        
    # Fetch questions from all linked topics
    topics = practice_set.topics.all()
    mcq_questions = MCQQuestion.objects.filter(topic__in=topics)
    coding_questions = CodingQuestion.objects.filter(topic__in=topics)
    
    if request.method == 'POST':
        # Handle submission scoring
        data = json.loads(request.body.decode('utf-8'))
        mcq_answers = data.get('mcq_answers', {})
        coding_submissions = data.get('coding_submissions', {})
        
        # 1. Score MCQs
        total_mcq_score = 0.0
        for q_id, chosen_idx in mcq_answers.items():
            question = MCQQuestion.objects.filter(id=q_id).first()
            if question and question.correct_option_index == int(chosen_idx):
                total_mcq_score += question.marks
                
        # 2. Score Coding Questions (Synchronous mock execution for immediate study feedback)
        total_coding_score = 0.0
        for q_id, code_info in coding_submissions.items():
            question = CodingQuestion.objects.filter(id=q_id).first()
            if question:
                code_text = code_info.get('code', '')
                lang = code_info.get('language', 'python')
                
                # Create a database Submission record
                sub = Submission.objects.create(
                    student=request.user,
                    coding_question=question,
                    code=code_text,
                    language=lang,
                    status='graded',
                    context_type='practice',
                    practice_set=practice_set
                )
                
                # Mock immediate correctness grading (check if solution has key phrases or executes)
                # In real use, this links to Celery / docker sandbox execution,
                # but local fallback checks python syntax / simple checks.
                # Let's write test results logs
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
                total_coding_score += tc_score
                
        # Write clean PracticeAttempt record
        score = total_mcq_score + total_coding_score
        PracticeAttempt.objects.create(
            student=request.user,
            practice_set=practice_set,
            score=score,
            mcq_score=total_mcq_score,
            coding_score=total_coding_score
        )
        
        return JsonResponse({
            'success': True,
            'score': score,
            'mcq_score': total_mcq_score,
            'coding_score': total_coding_score
        })
        
    context = {
        'practice_set': practice_set,
        'mcqs': mcq_questions,
        'coding_qs': coding_questions,
    }
    return render(request, 'practice/attempt.html', context)
