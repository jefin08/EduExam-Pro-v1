import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from content.models import PracticeCodingQuestion, ExamCodingQuestion
from .sandbox import run_custom_code, judge_code

@login_required
def run_custom_code_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required.'}, status=400)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
        
    code = data.get('code', '')
    language = data.get('language', 'python')
    custom_input = data.get('input', '')
    
    res = run_custom_code(code, language, custom_input)
    return JsonResponse(res)

@login_required
def run_sample_tests_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required.'}, status=400)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
        
    q_id = data.get('question_id')
    q_type = data.get('question_type', 'practice') # 'practice' or 'exam'
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    if q_type == 'practice':
        question = PracticeCodingQuestion.objects.filter(id=q_id).first()
    else:
        question = ExamCodingQuestion.objects.filter(id=q_id).first()
        
    if not question:
        return JsonResponse({'error': 'Question not found.'}, status=404)
        
    test_cases = question.sample_test_cases
    if not test_cases:
        return JsonResponse({
            'status': 'success',
            'results': []
        })
        
    success, compile_error, results = judge_code(
        code=code,
        language=language,
        test_cases=test_cases,
        time_limit=getattr(question, 'time_limit', 1.0),
        memory_limit=getattr(question, 'memory_limit', 256)
    )
    
    if not success:
        return JsonResponse({
            'status': 'compile_error',
            'compile_output': compile_error or "Compilation failed."
        })
        
    # Enrich results with expected inputs/outputs for student review
    enriched_results = []
    for res in results:
        idx = res['test_case_index']
        tc = test_cases[idx] if idx < len(test_cases) else {}
        
        enriched_results.append({
            'test_case_index': idx,
            'status': res['status'],
            'runtime_seconds': res['runtime_seconds'],
            'error_message': res['error_message'],
            'input': tc.get('input', ''),
            'expected': tc.get('output', '')
        })
        
    return JsonResponse({
        'status': 'success',
        'results': enriched_results
    })
