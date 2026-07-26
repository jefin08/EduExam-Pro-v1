import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import TeacherSignUpForm, StudentSignUpForm, UserSignInForm
from .models import User, Class
from content.models import Topic, TopicClassVisibility, PracticeMCQQuestion, PracticeCodingQuestion, ExamMCQQuestion, ExamCodingQuestion
from exams.models import Exam, ExamCode, OfficialGrade
from practice.models import PracticeSet, PracticeSetClassAssignment, PracticeAttempt

# Authentication Views
def signup_selection_view(request):
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    return render(request, 'accounts/signup_selection.html')

def teacher_signup_view(request):
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = TeacherSignUpForm(request.POST)
        if form.is_valid():
            department = form.cleaned_data['department']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Create user as inactive/pending-approval teacher
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='teacher',
                department=department,
                is_approved=False
            )
            
            messages.success(request, "Sign up request submitted successfully! Your account is pending admin approval.")
            return redirect('signin')
    else:
        form = TeacherSignUpForm()
        
    return render(request, 'accounts/signup.html', {'form': form, 'role_title': 'Teacher'})

def student_signup_view(request):
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            class_group = form.cleaned_data['class_group']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Create student user pending admin approval
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='student',
                class_group=class_group,
                is_approved=False
            )
            
            messages.success(request, "Sign up request submitted successfully! Your account is pending admin approval.")
            return redirect('signin')
    else:
        form = StudentSignUpForm()
        
    return render(request, 'accounts/signup_student.html', {'form': form})

def signin_view(request):
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = UserSignInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Enforce Teacher/Student approval check
                if user.role in ['teacher', 'student'] and not user.is_approved:
                    messages.error(request, "Access not granted by admin. Contact admin.")
                    return redirect('signin')
                
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect_to_dashboard(user)
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = UserSignInForm()
        
    return render(request, 'accounts/signin.html', {'form': form})

def signout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect('landing')

def redirect_to_dashboard(user):
    if user.role == 'admin':
        return redirect('/dashboard/admin/')
    elif user.role == 'teacher':
        return redirect('/dashboard/teacher/')
    else:
        return redirect('/dashboard/student/')

# ----------------- ADMIN DASHBOARD & ACTIONS -----------------

@login_required
def admin_dashboard_view(request):
    if request.user.role != 'admin':
        return redirect_to_dashboard(request.user)
    
    classes = Class.objects.all()
    teachers = User.objects.filter(role='teacher', is_approved=True)
    pending_teachers = User.objects.filter(role='teacher', is_approved=False)
    students = User.objects.filter(role='student', is_approved=True)
    pending_students = User.objects.filter(role='student', is_approved=False)
    
    context = {
        'classes': classes,
        'teachers': teachers,
        'pending_teachers': pending_teachers,
        'students': students,
        'pending_students': pending_students,
        'total_classes': classes.count(),
        'total_teachers': teachers.count(),
        'total_students': students.count(),
    }
    return render(request, 'dashboard/admin.html', context)

@login_required
def admin_approve_teacher(request, teacher_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
        
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')
    teacher.is_approved = True
    teacher.save()
    messages.success(request, f"Teacher account '{teacher.username}' has been approved and activated.")
    return redirect('/dashboard/admin/')

@login_required
def admin_approve_student(request, student_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
        
    student = get_object_or_404(User, id=student_id, role='student')
    student.is_approved = True
    student.save()
    messages.success(request, f"Student account '{student.username}' has been approved and activated.")
    return redirect('/dashboard/admin/')

@login_required
def admin_create_class(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    class_name = request.POST.get('class_name')
    if class_name:
        Class.objects.create(
            name=class_name
        )
        messages.success(request, f"Class '{class_name}' created successfully.")
    return redirect('/dashboard/admin/')

@login_required
def admin_create_teacher(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')
    
    if username and password:
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='teacher'
            )
            messages.success(request, f"Teacher account '{username}' created successfully.")
    return redirect('/dashboard/admin/')

@login_required
def admin_create_student(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')
    class_id = request.POST.get('class_id')
    
    if username and password and class_id:
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
        else:
            class_group = Class.objects.get(id=class_id)
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='student',
                class_group=class_group
            )
            messages.success(request, f"Student '{username}' enrolled in {class_group.name} successfully.")
    return redirect('/dashboard/admin/')

# ----------------- TEACHER DASHBOARD & ACTIONS -----------------

@login_required
def teacher_dashboard_view(request):
    if request.user.role != 'teacher':
        return redirect_to_dashboard(request.user)
    
    classes = Class.objects.all()
    topics = Topic.objects.filter(teacher=request.user)
    practice_mcqs = PracticeMCQQuestion.objects.filter(topic__teacher=request.user)
    exam_mcqs = ExamMCQQuestion.objects.filter(topic__teacher=request.user)
    practice_coding_qs = PracticeCodingQuestion.objects.filter(topic__teacher=request.user)
    exam_coding_qs = ExamCodingQuestion.objects.filter(topic__teacher=request.user)
    practice_sets = PracticeSet.objects.filter(teacher=request.user)
    exams = Exam.objects.filter(teacher=request.user)
    
    context = {
        'classes': classes,
        'topics': topics,
        'mcqs': list(practice_mcqs) + list(exam_mcqs),
        'coding_qs': list(practice_coding_qs) + list(exam_coding_qs),
        'practice_sets': practice_sets,
        'exams': exams,
        'now': timezone.now(),
    }
    return render(request, 'dashboard/teacher.html', context)

@login_required
def teacher_create_topic(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    name = request.POST.get('name')
    subject = request.POST.get('subject')
    class_ids = request.POST.getlist('class_ids')
    
    if name and subject:
        topic = Topic.objects.create(
            teacher=request.user,
            name=name,
            subject=subject
        )
        for class_id in class_ids:
            class_group = Class.objects.get(id=class_id)
            TopicClassVisibility.objects.create(topic=topic, class_group=class_group)
        messages.success(request, f"Topic '{name}' created with class visibility rules.")
    return redirect('/dashboard/teacher/')

@login_required
def teacher_create_mcq(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    topic_id = request.POST.get('topic_id')
    question_text = request.POST.get('question_text')
    opt1 = request.POST.get('option_0')
    opt2 = request.POST.get('option_1')
    opt3 = request.POST.get('option_2')
    opt4 = request.POST.get('option_3')
    correct_idx = request.POST.get('correct_option_index')
    marks = request.POST.get('marks', 1)
    difficulty = request.POST.get('difficulty', 'medium')
    explanation = request.POST.get('explanation', '')
    
    q_type = request.GET.get('type', 'practice')
    
    if topic_id and question_text and opt1 and opt2 and correct_idx is not None:
        topic = Topic.objects.get(id=topic_id)
        options = [opt1, opt2]
        if opt3: options.append(opt3)
        if opt4: options.append(opt4)
        
        ModelClass = ExamMCQQuestion if q_type == 'exam' else PracticeMCQQuestion
        ModelClass.objects.create(
            topic=topic,
            question_text=question_text,
            options=options,
            correct_option_index=int(correct_idx),
            marks=int(marks),
            difficulty=difficulty,
            explanation=explanation
        )
        messages.success(request, f"{q_type.title()} multiple-choice question added successfully.")
    return redirect('/dashboard/teacher/')

@login_required
def teacher_create_coding(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    topic_id = request.POST.get('topic_id')
    title = request.POST.get('title')
    description = request.POST.get('description')
    input_format = request.POST.get('input_format')
    output_format = request.POST.get('output_format')
    sample_input = request.POST.get('sample_input')
    sample_output = request.POST.get('sample_output')
    hidden_input = request.POST.get('hidden_input')
    hidden_output = request.POST.get('hidden_output')
    marks = request.POST.get('marks', 5)
    difficulty = request.POST.get('difficulty', 'medium')
    explanation = request.POST.get('explanation', '')
    
    q_type = request.GET.get('type', 'practice')

    if topic_id and title and description and sample_input and sample_output:
        topic = Topic.objects.get(id=topic_id)
        
        sample_cases = [{'input': sample_input, 'output': sample_output}]
        hidden_cases = [{'input': hidden_input or sample_input, 'output': hidden_output or sample_output}]
        
        ModelClass = ExamCodingQuestion if q_type == 'exam' else PracticeCodingQuestion
        kwargs = {
            'topic': topic,
            'title': title,
            'description': description,
            'input_format': input_format,
            'output_format': output_format,
            'sample_test_cases': sample_cases,
            'hidden_test_cases': hidden_cases,
            'marks': int(marks),
            'difficulty': difficulty,
        }
        if ModelClass == PracticeCodingQuestion:
            kwargs['explanation'] = explanation
        ModelClass.objects.create(**kwargs)
        messages.success(request, f"{q_type.title()} coding question '{title}' added successfully.")
    return redirect('/dashboard/teacher/')

@login_required
def teacher_create_practice(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    name = request.POST.get('name')
    topic_ids = request.POST.getlist('topic_ids')
    class_ids = request.POST.getlist('class_ids')
    reveal_rule = request.POST.get('reveal_rule', 'immediate')
    
    if name and topic_ids:
        practice_set = PracticeSet.objects.create(
            teacher=request.user,
            name=name,
            solution_reveal_rule=reveal_rule
        )
        # Assign topics
        for t_id in topic_ids:
            topic = Topic.objects.get(id=t_id)
            practice_set.topics.add(topic)
        
        # Assign class visibilities
        for c_id in class_ids:
            class_group = Class.objects.get(id=c_id)
            PracticeSetClassAssignment.objects.create(practice_set=practice_set, class_group=class_group)
        messages.success(request, f"Practice Set '{name}' published successfully.")
    return redirect('/dashboard/teacher/')

@login_required
def teacher_create_exam(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    name = request.POST.get('name')
    topic_ids = request.POST.getlist('topic_ids')
    class_ids = request.POST.getlist('class_ids')
    start_raw = request.POST.get('start_time')
    end_raw = request.POST.get('end_time')
    
    if name and topic_ids and start_raw and end_raw:
        from datetime import datetime
        try:
            naive_start = datetime.strptime(start_raw, '%Y-%m-%dT%H:%M')
            naive_end   = datetime.strptime(end_raw,   '%Y-%m-%dT%H:%M')
            
            aware_start = timezone.make_aware(naive_start)
            aware_end   = timezone.make_aware(naive_end)
            
            duration_minutes = int((aware_end - aware_start).total_seconds() // 60)
            if duration_minutes <= 0:
                duration_minutes = 1 # Fallback just in case
                
        except ValueError:
            messages.error(request, "Invalid date/time format.")
            return redirect('/dashboard/teacher/#exams-sec')

        exam = Exam.objects.create(
            teacher=request.user,
            name=name,
            duration_minutes=duration_minutes,
            start_time=aware_start,
            end_time=aware_end
        )
        # Link topics
        for t_id in topic_ids:
            topic = Topic.objects.get(id=t_id)
            exam.topics.add(topic)
            
        # Create Exam Code for target classes
        for c_id in class_ids:
            class_group = Class.objects.get(id=c_id)
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            ExamCode.objects.create(exam=exam, code=code, class_group=class_group)
            
        messages.success(request, f"Exam '{name}' scheduled successfully.")
    return redirect('/dashboard/teacher/')

# ----------------- STUDENT DASHBOARD & ACTIONS -----------------

@login_required
def student_dashboard_view(request):
    if request.user.role != 'student':
        return redirect_to_dashboard(request.user)
    
    class_group = request.user.class_group
    
    # Gating visibility check - strictly inherited from active Topic visibility mappings
    visible_topics = Topic.objects.filter(is_active=True, visibilities__class_group=class_group).distinct()
    practice_sets = PracticeSet.objects.filter(assignments__class_group=class_group).distinct()
    attempts = PracticeAttempt.objects.filter(student=request.user).order_by('-attempted_at')
    official_grades = OfficialGrade.objects.filter(student=request.user).order_by('-submitted_at')
    
    # Exams assigned to student's class (via exam codes)
    from exams.models import ExamCode
    upcoming_exams = ExamCode.objects.filter(
        class_group=class_group, is_active=True
    ).select_related('exam').order_by('exam__start_time')

    context = {
        'class_group': class_group,
        'visible_topics': visible_topics,
        'practice_sets': practice_sets,
        'attempts': attempts,
        'official_grades': official_grades,
        'upcoming_exams': upcoming_exams,
        'now': timezone.now(),
    }
    return render(request, 'dashboard/student.html', context)

@login_required
def student_join_exam(request):
    if request.user.role != 'student' or request.method != 'POST':
        return redirect('/dashboard/student/')
    
    code = request.POST.get('exam_code')
    if code:
        now = timezone.now()
        # Find active exam code
        exam_code_obj = ExamCode.objects.filter(
            code=code, 
            class_group=request.user.class_group, 
            is_active=True
        ).first()
        
        if not exam_code_obj:
            messages.error(request, "Invalid or inactive exam code.")
            return redirect('/dashboard/student/')
            
        exam = exam_code_obj.exam
        # Block entry before the exam window opens (allows joining 5 minutes early)
        from datetime import timedelta
        if now < (exam.start_time - timedelta(minutes=5)):
            local_start = timezone.localtime(exam.start_time)
            entry_time = timezone.localtime(exam.start_time - timedelta(minutes=5))
            messages.error(request, f"This exam hasn't started yet. Early entry opens at {entry_time.strftime('%I:%M %p')}.")
            return redirect('/dashboard/student/')

        # Block entry after the start time — students must join before or exactly at start time
        if now > exam.start_time:
            local_start = timezone.localtime(exam.start_time)
            messages.error(request, f"Entry closed. This exam started at {local_start.strftime('%I:%M %p')} and no late entries are allowed.")
            return redirect('/dashboard/student/')

        # Block if exam window has fully expired
        if now > exam.end_time:
            messages.error(request, "This exam has ended.")
            return redirect('/dashboard/student/')
            
        # Check attempts
        existing_grade = OfficialGrade.objects.filter(student=request.user, exam=exam).first()
        if existing_grade and existing_grade.is_submitted:
            messages.error(request, "You have already completed this exam.")
            return redirect('/dashboard/student/')
            
        # Redirect to start the actual exam take page
        return redirect(f'/exam/{exam.id}/')
        
    return redirect('/dashboard/student/')

@login_required
def teacher_toggle_visibility(request, topic_id, class_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
        
    topic = get_object_or_404(Topic, id=topic_id, teacher=request.user)
    class_group = get_object_or_404(Class, id=class_id)
    
    visibility = TopicClassVisibility.objects.filter(topic=topic, class_group=class_group).first()
    if visibility:
        visibility.delete()
        messages.success(request, f"Topic '{topic.name}' is now invisible to class '{class_group.name}'.")
    else:
        TopicClassVisibility.objects.create(topic=topic, class_group=class_group)
        messages.success(request, f"Topic '{topic.name}' is now visible to class '{class_group.name}'.")
        
    return redirect('/dashboard/teacher/')


@login_required
def teacher_edit_exam_schedule(request, exam_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')

    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)

    start_raw = request.POST.get('start_time')
    end_raw   = request.POST.get('end_time')

    if not start_raw or not end_raw:
        messages.error(request, "Both start and end date/time are required.")
        return redirect('/dashboard/teacher/#exams-sec')

    from datetime import datetime
    try:
        # datetime-local format: "YYYY-MM-DDTHH:MM"
        naive_start = datetime.strptime(start_raw, '%Y-%m-%dT%H:%M')
        naive_end   = datetime.strptime(end_raw,   '%Y-%m-%dT%H:%M')
    except ValueError:
        messages.error(request, "Invalid date/time format.")
        return redirect('/dashboard/teacher/#exams-sec')

    # Make timezone-aware
    aware_start = timezone.make_aware(naive_start)
    aware_end   = timezone.make_aware(naive_end)

    if aware_end <= aware_start:
        messages.error(request, "End time must be after start time.")
        return redirect('/dashboard/teacher/#exams-sec')

    # Auto-calculate duration from time difference
    duration_minutes = int((aware_end - aware_start).total_seconds() // 60)

    exam.start_time       = aware_start
    exam.end_time         = aware_end
    exam.duration_minutes = duration_minutes
    exam.save()

    messages.success(request, f"Schedule updated for '{exam.name}' — duration set to {duration_minutes} mins.")
    return redirect('/dashboard/teacher/#exams-sec')

@login_required
def teacher_topic_questions(request, topic_id):
    if request.user.role != 'teacher':
        return redirect_to_dashboard(request.user)
    
    topic = get_object_or_404(Topic, id=topic_id, teacher=request.user)
    practice_mcqs = PracticeMCQQuestion.objects.filter(topic=topic).order_by('-created_at')
    exam_mcqs = ExamMCQQuestion.objects.filter(topic=topic).order_by('-created_at')
    practice_coding_qs = PracticeCodingQuestion.objects.filter(topic=topic).order_by('-created_at')
    exam_coding_qs = ExamCodingQuestion.objects.filter(topic=topic).order_by('-created_at')
    
    total_mcqs = practice_mcqs.count() + exam_mcqs.count()
    total_coding = practice_coding_qs.count() + exam_coding_qs.count()
    total_questions = total_mcqs + total_coding
    
    # Calculate difficulties across all 4 sets
    easy_count = practice_mcqs.filter(difficulty='easy').count() + exam_mcqs.filter(difficulty='easy').count() + practice_coding_qs.filter(difficulty='easy').count() + exam_coding_qs.filter(difficulty='easy').count()
    medium_count = practice_mcqs.filter(difficulty='medium').count() + exam_mcqs.filter(difficulty='medium').count() + practice_coding_qs.filter(difficulty='medium').count() + exam_coding_qs.filter(difficulty='medium').count()
    hard_count = practice_mcqs.filter(difficulty='hard').count() + exam_mcqs.filter(difficulty='hard').count() + practice_coding_qs.filter(difficulty='hard').count() + exam_coding_qs.filter(difficulty='hard').count()
    
    context = {
        'topic': topic,
        'practice_mcqs': practice_mcqs,
        'exam_mcqs': exam_mcqs,
        'practice_coding_qs': practice_coding_qs,
        'exam_coding_qs': exam_coding_qs,
        'stats': {
            'total': total_questions,
            'mcq': total_mcqs,
            'coding': total_coding,
            'easy': easy_count,
            'medium': medium_count,
            'hard': hard_count,
        }
    }
    return render(request, 'dashboard/teacher_topic_questions.html', context)

@login_required
def teacher_delete_mcq(request, question_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    q_type = request.GET.get('type', 'practice')
    ModelClass = ExamMCQQuestion if q_type == 'exam' else PracticeMCQQuestion
    question = get_object_or_404(ModelClass, id=question_id, topic__teacher=request.user)
    topic_id = question.topic.id
    question.delete()
    messages.success(request, f"{q_type.title()} multiple-choice question deleted successfully.")
    return redirect(f'/dashboard/teacher/topic/{topic_id}/questions/')

@login_required
def teacher_delete_coding(request, question_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    q_type = request.GET.get('type', 'practice')
    ModelClass = ExamCodingQuestion if q_type == 'exam' else PracticeCodingQuestion
    question = get_object_or_404(ModelClass, id=question_id, topic__teacher=request.user)
    topic_id = question.topic.id
    title = question.title
    question.delete()
    messages.success(request, f"{q_type.title()} coding question '{title}' deleted successfully.")
    return redirect(f'/dashboard/teacher/topic/{topic_id}/questions/')

@login_required
def teacher_edit_mcq(request, question_id):
    if request.user.role != 'teacher':
        return redirect('/dashboard/teacher/')
        
    q_type = request.GET.get('type', 'practice')
    ModelClass = ExamMCQQuestion if q_type == 'exam' else PracticeMCQQuestion
    question = get_object_or_404(ModelClass, id=question_id, topic__teacher=request.user)
    
    if request.method == 'POST':
        question.question_text = request.POST.get('question_text')
        
        opt1 = request.POST.get('option_0')
        opt2 = request.POST.get('option_1')
        opt3 = request.POST.get('option_2')
        opt4 = request.POST.get('option_3')
        
        options = [opt1, opt2]
        if opt3: options.append(opt3)
        if opt4: options.append(opt4)
        
        question.options = options
        question.correct_option_index = int(request.POST.get('correct_option_index', 0))
        question.marks = int(request.POST.get('marks', 1))
        question.difficulty = request.POST.get('difficulty', 'medium')
        question.explanation = request.POST.get('explanation', '')
        
        question.save()
        messages.success(request, f"{q_type.title()} multiple-choice question updated successfully.")
        return redirect(f'/dashboard/teacher/topic/{question.topic.id}/questions/')
        
    return render(request, 'dashboard/teacher_edit_mcq.html', {'question': question, 'q_type': q_type})

@login_required
def teacher_edit_coding(request, question_id):
    if request.user.role != 'teacher':
        return redirect('/dashboard/teacher/')
        
    q_type = request.GET.get('type', 'practice')
    ModelClass = ExamCodingQuestion if q_type == 'exam' else PracticeCodingQuestion
    question = get_object_or_404(ModelClass, id=question_id, topic__teacher=request.user)
    
    if request.method == 'POST':
        question.title = request.POST.get('title')
        question.description = request.POST.get('description')
        question.input_format = request.POST.get('input_format')
        question.output_format = request.POST.get('output_format')
        
        sample_input = request.POST.get('sample_input')
        sample_output = request.POST.get('sample_output')
        hidden_input = request.POST.get('hidden_input')
        hidden_output = request.POST.get('hidden_output')
        
        question.sample_test_cases = [{'input': sample_input, 'output': sample_output}]
        question.hidden_test_cases = [{'input': hidden_input or sample_input, 'output': hidden_output or sample_output}]
        
        question.marks = int(request.POST.get('marks', 5))
        question.difficulty = request.POST.get('difficulty', 'medium')
        
        if hasattr(question, 'explanation'):
            question.explanation = request.POST.get('explanation', '')
        
        question.save()
        messages.success(request, f"{q_type.title()} coding question '{question.title}' updated successfully.")
        return redirect(f'/dashboard/teacher/topic/{question.topic.id}/questions/')
        
    return render(request, 'dashboard/teacher_edit_coding.html', {'question': question, 'q_type': q_type})
