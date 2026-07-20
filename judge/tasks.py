from celery import shared_task
from .models import Submission, TestCaseResult
from .sandbox import judge_code

@shared_task
def run_submission_task(submission_id):
    """
    Asynchronous Celery Task: Evaluates a student's code submission
    and saves results inside the database models.
    """
    try:
        sub = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return
        
    sub.status = 'judging'
    sub.save()
    
    question = sub.coding_question
    # Merge sample and hidden test cases for evaluation
    test_cases = question.sample_test_cases + question.hidden_test_cases
    
    # Run sandbox evaluation
    compile_ok, error_log, results = judge_code(
        code=sub.code,
        language=sub.language,
        test_cases=test_cases,
        time_limit=question.time_limit,
        memory_limit=question.memory_limit
    )
    
    if not compile_ok:
        sub.status = 'compile_error'
        sub.compile_output = error_log or "Compilation failed."
        sub.score = 0.0
        sub.save()
        return
        
    # Write test case result logs
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
            
    # Calculate score based on passed test cases ratio
    passed_ratio = total_passed / total_tests if total_tests > 0 else 0
    sub.score = round(question.marks * passed_ratio, 2)
    sub.status = 'graded'
    sub.save()
    
    # Update contextual scores (if exam/practice attempt needs syncing)
    # This task normally triggers WebSockets pushes to update the student UI in real time.
    print(f"Submission {submission_id} evaluated: {total_passed}/{total_tests} passed. Score: {sub.score}")
