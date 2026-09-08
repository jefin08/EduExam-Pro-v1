import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import TeacherSignUpForm, StudentSignUpForm, UserSignInForm
from .models import User, Class, Department
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
            full_name = form.cleaned_data['full_name'].strip()
            name_parts = full_name.split(None, 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            department = form.cleaned_data['department']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Create user as inactive/pending-approval teacher
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='teacher',
                department=department,
                is_approved=False
            )
            
            messages.success(request, "Sign up request submitted successfully! Your account is pending admin approval. You will be able to sign in once an administrator approves your account.")
            return redirect('/signin/?pending=true')
    else:
        form = TeacherSignUpForm()
        
    return render(request, 'accounts/signup.html', {'form': form, 'role_title': 'Teacher'})

def student_signup_view(request):
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip()
            name_parts = full_name.split(None, 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            class_group = form.cleaned_data['class_group']
            department = form.cleaned_data['department']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Create student user pending admin approval
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='student',
                class_group=class_group,
                department=department,
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
    departments = Department.objects.all().order_by('name')
    teachers = User.objects.filter(role='teacher', is_approved=True)
    pending_teachers = User.objects.filter(role='teacher', is_approved=False)
    students = User.objects.filter(role='student', is_approved=True)
    pending_students = User.objects.filter(role='student', is_approved=False)
    
    context = {
        'classes': classes,
        'departments': departments,
        'teachers': teachers,
        'pending_teachers': pending_teachers,
        'students': students,
        'pending_students': pending_students,
        'total_classes': classes.count(),
        'total_teachers': teachers.count(),
        'total_students': students.count(),
    }
    return render(request, 'dashboard/admin.html', context)

from django.http import JsonResponse

@login_required
def admin_pending_count_api(request):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    pending_teachers_count = User.objects.filter(role='teacher', is_approved=False).count()
    pending_students_count = User.objects.filter(role='student', is_approved=False).count()
    total_pending_count = pending_teachers_count + pending_students_count
    
    return JsonResponse({
        'pending_teachers_count': pending_teachers_count,
        'pending_students_count': pending_students_count,
        'total_pending_count': total_pending_count
    })

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
    department = request.POST.get('department')
    
    if username and password:
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='teacher',
                department=department,
                is_approved=True
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
    department = request.POST.get('department')
    
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
                class_group=class_group,
                department=department,
                is_approved=True
            )
            messages.success(request, f"Student '{username}' enrolled in {class_group.name} successfully.")
    return redirect('/dashboard/admin/')

@login_required
def admin_create_department(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    dept_name = request.POST.get('department_name')
    if dept_name:
        dept_name = dept_name.strip()
        dept, created = Department.objects.get_or_create(name=dept_name)
        if created:
            messages.success(request, f"Department '{dept_name}' created successfully.")
        else:
            messages.warning(request, f"Department '{dept_name}' already exists.")
    return redirect('/dashboard/admin/')

# ----------------- TEACHER DASHBOARD & ACTIONS -----------------

@login_required
def teacher_dashboard_view(request):
    if request.user.role != 'teacher':
        return redirect_to_dashboard(request.user)
    
    classes = Class.objects.all()
    topics = Topic.objects.filter(teacher=request.user)
    
    practice_mcqs = PracticeMCQQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at')
    exam_mcqs = ExamMCQQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at')
    practice_coding_qs = PracticeCodingQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at')
    exam_coding_qs = ExamCodingQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at')
    practice_sets = PracticeSet.objects.filter(teacher=request.user).prefetch_related('assignments__class_group', 'topics')
    exams = Exam.objects.filter(teacher=request.user).prefetch_related('codes__class_group', 'topics')
    all_official_grades = OfficialGrade.objects.filter(exam__teacher=request.user).select_related('student', 'student__class_group', 'exam').order_by('-submitted_at')
    
    context = {
        'classes': classes,
        'topics': topics,
        'practice_mcqs': practice_mcqs,
        'exam_mcqs': exam_mcqs,
        'practice_coding_qs': practice_coding_qs,
        'exam_coding_qs': exam_coding_qs,
        'practice_sets': practice_sets,
        'exams': exams,
        'all_official_grades': all_official_grades,
        'now': timezone.now(),
    }
    return render(request, 'dashboard/teacher.html', context)

@login_required
def teacher_exams_view(request):
    return redirect('/dashboard/teacher/#exams')

@login_required
def teacher_practice_view(request):
    return redirect('/dashboard/teacher/#practice')

@login_required
def teacher_create_topic(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    name = request.POST.get('name')
    subject = request.POST.get('subject')
    class_ids = request.POST.getlist('class_ids')
    purpose = request.POST.get('purpose', 'both')
    
    if name and subject:
        topic = Topic.objects.create(
            teacher=request.user,
            name=name,
            subject=subject,
            purpose=purpose
        )
        for class_id in class_ids:
            class_group = Class.objects.get(id=class_id)
            TopicClassVisibility.objects.create(topic=topic, class_group=class_group)
        messages.success(request, f"Topic '{name}' created with class visibility rules.")
    return redirect('/dashboard/teacher/')

@login_required
def teacher_edit_topic(request, topic_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    topic = get_object_or_404(Topic, id=topic_id, teacher=request.user)
    name = request.POST.get('name')
    subject = request.POST.get('subject')
    purpose = request.POST.get('purpose')
    
    if name and subject and purpose:
        topic.name = name
        topic.subject = subject
        topic.purpose = purpose
        topic.save()
        messages.success(request, f"Topic '{name}' updated successfully.")
    else:
        messages.error(request, "Invalid input data.")
        
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
    
    q_type = request.GET.get('type') or request.POST.get('question_type') or 'practice'
    
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
    return redirect('/dashboard/teacher/#questions')

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
    starter_code = request.POST.get('starter_code', '')
    time_limit = request.POST.get('time_limit', 2)
    memory_limit = request.POST.get('memory_limit', 256)
    marks = request.POST.get('marks', 5)
    difficulty = request.POST.get('difficulty', 'medium')
    explanation = request.POST.get('explanation', '')
    
    q_type = request.GET.get('type') or request.POST.get('question_type') or 'practice'

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
            'starter_code': starter_code,
            'time_limit': int(time_limit) if str(time_limit).isdigit() else 2,
            'memory_limit': int(memory_limit) if str(memory_limit).isdigit() else 256,
            'marks': int(marks),
            'difficulty': difficulty,
        }
        if ModelClass == PracticeCodingQuestion:
            kwargs['explanation'] = explanation
        ModelClass.objects.create(**kwargs)
        messages.success(request, f"{q_type.title()} coding question '{title}' added successfully.")
    return redirect('/dashboard/teacher/#questions')

@login_required
def teacher_create_practice(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    name = request.POST.get('name')
    topic_ids = request.POST.getlist('topic_ids')
    class_ids = request.POST.getlist('class_ids')
    reveal_rule = request.POST.get('reveal_rule', 'immediate')
    
    if name and topic_ids:
        # Check if selected topics contain 0 questions for practice
        total_questions = 0
        for t_id in topic_ids:
            topic = Topic.objects.get(id=t_id)
            total_questions += topic.practice_mcq_questions.count() + topic.practice_coding_questions.count()
        
        if total_questions == 0:
            messages.error(request, "Cannot create practice set: The selected topics do not contain any practice questions.")
            return redirect('/dashboard/teacher/#practice')

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
    return redirect('/dashboard/teacher/#practice')

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
        # Check if selected topics contain 0 questions for exam
        total_questions = 0
        for t_id in topic_ids:
            topic = Topic.objects.get(id=t_id)
            total_questions += topic.exam_mcq_questions.count() + topic.exam_coding_questions.count()
        
        if total_questions == 0:
            messages.error(request, "Cannot schedule exam: The selected topics do not contain any exam questions.")
            return redirect('/dashboard/teacher/exams/')

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
            return redirect('/dashboard/teacher/#exams')

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
    return redirect('/dashboard/teacher/#exams')

# ----------------- STUDENT DASHBOARD & ACTIONS -----------------

@login_required
def student_dashboard_view(request):
    if request.user.role != 'student':
        return redirect_to_dashboard(request.user)
    
    class_group = request.user.class_group
    
    # Gating visibility check - strictly inherited from active Topic visibility mappings
    # Exclude topics designed purely for exams from the practice view
    visible_topics = Topic.objects.filter(is_active=True, visibilities__class_group=class_group).exclude(purpose='exam').distinct()
    visible_topic_ids = visible_topics.values_list('id', flat=True)
    
    # Show practice sets only if ALL their topics are visible to the student's class group
    practice_sets = PracticeSet.objects.filter(assignments__class_group=class_group).exclude(
        topics__in=Topic.objects.exclude(id__in=visible_topic_ids)
    ).distinct()
    
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
        'practice_sets': practice_sets[:3],
        'attempts': attempts,
        'official_grades': official_grades[:3],
        'upcoming_exams': upcoming_exams[:3],
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
        # Block entry before the exam window opens (allows joining 15 minutes early)
        from datetime import timedelta
        if now < (exam.start_time - timedelta(minutes=15)):
            local_start = timezone.localtime(exam.start_time)
            entry_time = timezone.localtime(exam.start_time - timedelta(minutes=15))
            messages.error(request, f"This exam hasn't started yet. Early entry opens at {entry_time.strftime('%I:%M %p')}.")
            return redirect('/dashboard/student/')

        # Block entry after the 15-minute late-entry window
        late_deadline = exam.start_time + timedelta(minutes=15)
        if now > late_deadline:
            local_start = timezone.localtime(exam.start_time)
            messages.error(request, f"Entry closed. The 15-minute late-entry window for this exam has ended. It started at {local_start.strftime('%I:%M %p')}.")
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
def student_scheduled_exams_view(request):
    if request.user.role != 'student':
        return redirect_to_dashboard(request.user)
    
    class_group = request.user.class_group
    from exams.models import ExamCode
    upcoming_exams = ExamCode.objects.filter(
        class_group=class_group, is_active=True
    ).select_related('exam').order_by('exam__start_time')
    
    context = {
        'upcoming_exams': upcoming_exams,
        'now': timezone.now(),
    }
    return render(request, 'dashboard/student_scheduled_exams.html', context)

@login_required
def student_practice_sets_view(request):
    if request.user.role != 'student':
        return redirect_to_dashboard(request.user)
    
    class_group = request.user.class_group
    visible_topics = Topic.objects.filter(is_active=True, visibilities__class_group=class_group).exclude(purpose='exam').distinct()
    visible_topic_ids = visible_topics.values_list('id', flat=True)
    
    practice_sets = PracticeSet.objects.filter(assignments__class_group=class_group).exclude(
        topics__in=Topic.objects.exclude(id__in=visible_topic_ids)
    ).distinct()
    
    context = {
        'practice_sets': practice_sets,
    }
    return render(request, 'dashboard/student_practice_sets.html', context)

@login_required
def student_assessment_history_view(request):
    if request.user.role != 'student':
        return redirect_to_dashboard(request.user)
    
    official_grades = OfficialGrade.objects.filter(student=request.user).order_by('-submitted_at')
    
    context = {
        'official_grades': official_grades,
    }
    return render(request, 'dashboard/student_assessment_history.html', context)

@login_required
def student_profile_view(request):
    if request.user.role != 'student':
        return redirect_to_dashboard(request.user)
    
    context = {
        'student': request.user
    }
    return render(request, 'dashboard/student_profile.html', context)

@login_required
def teacher_profile_view(request):
    if request.user.role != 'teacher':
        return redirect_to_dashboard(request.user)
    
    context = {
        'teacher': request.user
    }
    return render(request, 'dashboard/teacher_profile.html', context)

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
def teacher_practice_toggle_visibility(request, practice_set_id, class_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/#practice')
        
    practice_set = get_object_or_404(PracticeSet, id=practice_set_id, teacher=request.user)
    class_group = get_object_or_404(Class, id=class_id)
    
    assignment = PracticeSetClassAssignment.objects.filter(practice_set=practice_set, class_group=class_group).first()
    if assignment:
        assignment.delete()
        messages.success(request, f"Practice Set '{practice_set.name}' unassigned from class '{class_group.name}'.")
    else:
        PracticeSetClassAssignment.objects.create(practice_set=practice_set, class_group=class_group)
        messages.success(request, f"Practice Set '{practice_set.name}' assigned to class '{class_group.name}'.")
        
    return redirect('/dashboard/teacher/#practice')

@login_required
def teacher_toggle_exam_code_visibility(request, exam_code_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/#results')
        
    exam_code = get_object_or_404(ExamCode, id=exam_code_id, exam__teacher=request.user)
    exam_code.is_active = not exam_code.is_active
    exam_code.save()
    status_str = "unlocked/active" if exam_code.is_active else "locked/hidden"
    messages.success(request, f"Exam results & access for class '{exam_code.class_group.name}' updated to {status_str}.")
    return redirect('/dashboard/teacher/#results')

@login_required
def teacher_edit_exam_schedule(request, exam_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/#exams')

    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)

    start_raw = request.POST.get('start_time')
    end_raw   = request.POST.get('end_time')

    if not start_raw or not end_raw:
        messages.error(request, "Both start and end date/time are required.")
        return redirect('/dashboard/teacher/#exams')

    from datetime import datetime
    try:
        # datetime-local format: "YYYY-MM-DDTHH:MM"
        naive_start = datetime.strptime(start_raw, '%Y-%m-%dT%H:%M')
        naive_end   = datetime.strptime(end_raw,   '%Y-%m-%dT%H:%M')
    except ValueError:
        messages.error(request, "Invalid date/time format.")
        return redirect('/dashboard/teacher/#exams')

    # Make timezone-aware
    aware_start = timezone.make_aware(naive_start)
    aware_end   = timezone.make_aware(naive_end)

    if aware_end <= aware_start:
        messages.error(request, "End time must be after start time.")
        return redirect('/dashboard/teacher/#exams')

    # Auto-calculate duration from time difference
    duration_minutes = int((aware_end - aware_start).total_seconds() // 60)

    exam.start_time       = aware_start
    exam.end_time         = aware_end
    exam.duration_minutes = duration_minutes
    exam.save()

    messages.success(request, f"Schedule updated for '{exam.name}' — duration set to {duration_minutes} mins.")
    return redirect('/dashboard/teacher/#exams')

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
    referer = request.META.get('HTTP_REFERER', '')
    if 'topic' not in referer:
        return redirect('/dashboard/teacher/#questions')
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
    referer = request.META.get('HTTP_REFERER', '')
    if 'topic' not in referer:
        return redirect('/dashboard/teacher/#questions')
    return redirect(f'/dashboard/teacher/topic/{topic_id}/questions/')

@login_required
def teacher_import_practice_to_exam(request, topic_id):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
        
    topic = get_object_or_404(Topic, id=topic_id, teacher=request.user)
    
    # 1. Parse MCQs to import
    mcq_ids = request.POST.getlist('import_mcq_ids')
    for q_id in mcq_ids:
        practice_q = PracticeMCQQuestion.objects.filter(id=q_id, topic=topic).first()
        if practice_q:
            # Retrieve edited values from POST data
            q_text = request.POST.get(f'mcq_text_{q_id}', practice_q.question_text)
            q_marks = request.POST.get(f'mcq_marks_{q_id}', practice_q.marks)
            q_diff = request.POST.get(f'mcq_difficulty_{q_id}', practice_q.difficulty)
            
            # Duplicate as Exam question
            ExamMCQQuestion.objects.create(
                topic=topic,
                question_text=q_text,
                options=practice_q.options,
                correct_option_index=practice_q.correct_option_index,
                explanation=practice_q.explanation,
                marks=int(q_marks) if q_marks.isdigit() else practice_q.marks,
                difficulty=q_diff,
                tags=practice_q.tags
            )
            
    # 2. Parse Coding Questions to import
    coding_ids = request.POST.getlist('import_coding_ids')
    for q_id in coding_ids:
        practice_q = PracticeCodingQuestion.objects.filter(id=q_id, topic=topic).first()
        if practice_q:
            # Retrieve edited values from POST data
            q_title = request.POST.get(f'coding_title_{q_id}', practice_q.title)
            q_desc = request.POST.get(f'coding_desc_{q_id}', practice_q.description)
            q_marks = request.POST.get(f'coding_marks_{q_id}', practice_q.marks)
            q_diff = request.POST.get(f'coding_difficulty_{q_id}', practice_q.difficulty)
            
            # Duplicate as Exam question
            ExamCodingQuestion.objects.create(
                topic=topic,
                title=q_title,
                description=q_desc,
                input_format=practice_q.input_format,
                output_format=practice_q.output_format,
                sample_test_cases=practice_q.sample_test_cases,
                hidden_test_cases=practice_q.hidden_test_cases,
                starter_code=practice_q.starter_code,
                time_limit=practice_q.time_limit,
                memory_limit=practice_q.memory_limit,
                marks=int(q_marks) if q_marks.isdigit() else practice_q.marks,
                difficulty=q_diff,
                tags=practice_q.tags
            )
            
    messages.success(request, "Selected practice questions imported to exam questions successfully.")
    referer = request.META.get('HTTP_REFERER', '')
    if 'topic' not in referer:
        return redirect('/dashboard/teacher/#questions')
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
        return redirect('/dashboard/teacher/#questions')
        
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
        
        question.starter_code = request.POST.get('starter_code', '')
        time_lim = request.POST.get('time_limit', 2)
        mem_lim = request.POST.get('memory_limit', 256)
        question.time_limit = int(time_lim) if str(time_lim).isdigit() else 2
        question.memory_limit = int(mem_lim) if str(mem_lim).isdigit() else 256
        
        question.marks = int(request.POST.get('marks', 5))
        question.difficulty = request.POST.get('difficulty', 'medium')
        
        if hasattr(question, 'explanation'):
            question.explanation = request.POST.get('explanation', '')
        
        question.save()
        messages.success(request, f"{q_type.title()} coding question '{question.title}' updated successfully.")
        return redirect('/dashboard/teacher/#questions')
        
    return render(request, 'dashboard/teacher_edit_coding.html', {'question': question, 'q_type': q_type})


def parse_bulk_text(bulk_text):
    import re
    # Split text into blocks by "Question No:"
    blocks = re.split(r'(?i)Question\s+No:\s*\d*', bulk_text)
    
    parsed_questions = []
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # Extract fields
        q_type = None
        q_text = ""
        options = []
        correct_val = ""
        explanation = ""
        marks = 5
        difficulty = "easy"
        
        # Coding fields
        title = ""
        description = ""
        input_format = ""
        output_format = ""
        sample_input = ""
        sample_output = ""
        hidden_input = ""
        hidden_output = ""
        starter_code = ""
        
        # Read line by line
        current_multiline_field = None
        multiline_buffer = []
        
        def flush_multiline():
            nonlocal current_multiline_field, multiline_buffer, q_text, description, input_format, output_format, sample_input, sample_output, hidden_input, hidden_output, starter_code, explanation
            val = "\n".join(multiline_buffer).strip()
            if not val:
                return
            if current_multiline_field == 'question':
                q_text = val
            elif current_multiline_field == 'description':
                description = val
            elif current_multiline_field == 'input_format':
                input_format = val
            elif current_multiline_field == 'output_format':
                output_format = val
            elif current_multiline_field == 'sample_input':
                sample_input = val
            elif current_multiline_field == 'sample_output':
                sample_output = val
            elif current_multiline_field == 'hidden_input':
                hidden_input = val
            elif current_multiline_field == 'hidden_output':
                hidden_output = val
            elif current_multiline_field == 'starter_code':
                starter_code = val
            elif current_multiline_field == 'explanation':
                explanation = val
            multiline_buffer = []
            current_multiline_field = None

        for line in block.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
                
            lower_line = line_str.lower()
            
            # Type:
            if lower_line.startswith('type:'):
                flush_multiline()
                q_type = line_str[5:].strip().upper() # MCQ or CODING
                
            # Question:
            elif lower_line.startswith('question:'):
                flush_multiline()
                current_multiline_field = 'question'
                multiline_buffer.append(line_str[9:].strip())
                
            # Correct:
            elif lower_line.startswith('correct:'):
                flush_multiline()
                correct_val = line_str[8:].strip().upper()
                
            # Explanation:
            elif lower_line.startswith('explanation:'):
                flush_multiline()
                current_multiline_field = 'explanation'
                multiline_buffer.append(line_str[12:].strip())
                
            # Marks:
            elif lower_line.startswith('marks:'):
                flush_multiline()
                try:
                    marks = int(line_str[6:].strip())
                except ValueError:
                    marks = 5
                    
            # Difficulty:
            elif lower_line.startswith('difficulty:'):
                flush_multiline()
                difficulty = line_str[11:].strip().lower()
                
            # Coding Fields:
            elif lower_line.startswith('title:'):
                flush_multiline()
                title = line_str[6:].strip()
                
            elif lower_line.startswith('description:'):
                flush_multiline()
                current_multiline_field = 'description'
                multiline_buffer.append(line_str[12:].strip())
                
            elif lower_line.startswith('input format:'):
                flush_multiline()
                current_multiline_field = 'input_format'
                multiline_buffer.append(line_str[13:].strip())
                
            elif lower_line.startswith('output format:'):
                flush_multiline()
                current_multiline_field = 'output_format'
                multiline_buffer.append(line_str[14:].strip())
                
            elif lower_line.startswith('sample input:'):
                flush_multiline()
                current_multiline_field = 'sample_input'
                multiline_buffer.append(line_str[13:].strip())
                
            elif lower_line.startswith('sample output:'):
                flush_multiline()
                current_multiline_field = 'sample_output'
                multiline_buffer.append(line_str[14:].strip())
                
            elif lower_line.startswith('hidden input:'):
                flush_multiline()
                current_multiline_field = 'hidden_input'
                multiline_buffer.append(line_str[13:].strip())
                
            elif lower_line.startswith('hidden output:'):
                flush_multiline()
                current_multiline_field = 'hidden_output'
                multiline_buffer.append(line_str[14:].strip())
                
            elif lower_line.startswith('starter code:'):
                flush_multiline()
                current_multiline_field = 'starter_code'
                multiline_buffer.append(line_str[13:].strip())
                
            # Options (A), B), C)... or A., B., C....)
            elif re.match(r'^[A-Z][\)\.]', line_str):
                flush_multiline()
                opt_match = re.match(r'^([A-Z])[\)\.]\s*(.*)$', line_str)
                if opt_match:
                    opt_letter = opt_match.group(1)
                    opt_text = opt_match.group(2).strip()
                    options.append((opt_letter, opt_text))
            
            # If we are inside a multiline field, continue appending
            elif current_multiline_field:
                multiline_buffer.append(line)
                
        flush_multiline()
        
        # Validate and prepare question dict
        warnings = []
        if not q_type or q_type not in ['MCQ', 'CODING']:
            warnings.append("Invalid or missing Type. Must be 'MCQ' or 'Coding'.")
            q_type = q_type or 'MCQ'
            
        if q_type == 'MCQ':
            if not q_text:
                warnings.append("Missing question text.")
            if len(options) < 2:
                warnings.append("MCQ must have at least 2 options.")
            
            # Resolve correct option index
            correct_idx = -1
            if correct_val:
                for idx, (letter, text) in enumerate(options):
                    if letter == correct_val:
                        correct_idx = idx
                        break
                if correct_idx == -1:
                    warnings.append(f"Correct option '{correct_val}' was not found in parsed options.")
            else:
                warnings.append("Missing correct option (e.g., 'Correct: B').")
                
            parsed_questions.append({
                'type': 'MCQ',
                'question_text': q_text,
                'options': [opt[1] for opt in options],
                'correct_option_index': correct_idx,
                'explanation': explanation,
                'marks': marks,
                'difficulty': difficulty,
                'warnings': warnings,
                'has_warnings': len(warnings) > 0
            })
            
        elif q_type == 'CODING':
            if not title:
                warnings.append("Missing title for coding question.")
            if not description:
                warnings.append("Missing description for coding question.")
            if not sample_input or not sample_output:
                warnings.append("Missing Sample Input or Sample Output.")
            if not hidden_input or not hidden_output:
                warnings.append("Missing Hidden Input or Hidden Output.")
                
            parsed_questions.append({
                'type': 'CODING',
                'title': title,
                'description': description,
                'input_format': input_format,
                'output_format': output_format,
                'sample_input': sample_input,
                'sample_output': sample_output,
                'hidden_input': hidden_input,
                'hidden_output': hidden_output,
                'starter_code': starter_code,
                'explanation': explanation,
                'marks': marks,
                'difficulty': difficulty,
                'warnings': warnings,
                'has_warnings': len(warnings) > 0
            })
            
    return parsed_questions


@login_required
def teacher_bulk_upload_view(request):
    if request.user.role != 'teacher':
        return redirect_to_dashboard(request.user)
        
    topics = Topic.objects.filter(teacher=request.user)
    classes = Class.objects.all()
    
    if request.method == 'POST':
        topic_id = request.POST.get('topic_id')
        bulk_text = request.POST.get('bulk_text', '')
        
        if 'bulk_file' in request.FILES:
            file_obj = request.FILES['bulk_file']
            try:
                bulk_text = file_obj.read().decode('utf-8')
            except Exception:
                pass
                
        if not topic_id:
            messages.error(request, "Please select a topic.")
            return redirect('/dashboard/teacher/#questions')
            
        topic = get_object_or_404(Topic, id=topic_id, teacher=request.user)
        parsed_questions = parse_bulk_text(bulk_text)
        
        practice_mcqs = PracticeMCQQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at')
        exam_mcqs = ExamMCQQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at')
        practice_coding_qs = PracticeCodingQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at')
        exam_coding_qs = ExamCodingQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at')
        
        context = {
            'classes': classes,
            'topics': topics,
            'practice_mcqs': practice_mcqs,
            'exam_mcqs': exam_mcqs,
            'practice_coding_qs': practice_coding_qs,
            'exam_coding_qs': exam_coding_qs,
            'open_bulk_verify': True,
            'bulk_topic': topic,
            'parsed_questions': parsed_questions,
            'bulk_text': bulk_text,
        }
        return render(request, 'dashboard/teacher.html', context)
        
    return redirect('/dashboard/teacher/#questions')


@login_required
def teacher_bulk_save_view(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
        
    topic_id = request.POST.get('topic_id')
    topic = get_object_or_404(Topic, id=topic_id, teacher=request.user)
    
    index = 0
    created_mcq_ids = []
    created_coding_ids = []
    
    while True:
        q_type = request.POST.get(f'type_{index}')
        if not q_type:
            if index > 150:
                break
            index += 1
            continue
            
        include = request.POST.get(f'include_{index}')
        if not include:
            index += 1
            continue
            
        marks = int(request.POST.get(f'marks_{index}', 5))
        difficulty = request.POST.get(f'difficulty_{index}', 'easy')
        explanation = request.POST.get(f'explanation_{index}', '')
        
        if q_type == 'MCQ':
            q_text = request.POST.get(f'question_text_{index}', '').strip()
            
            options = []
            opt_idx = 0
            while True:
                opt_val = request.POST.get(f'option_{index}_{opt_idx}')
                if opt_val is None:
                    break
                opt_val = opt_val.strip()
                if opt_val:
                    options.append(opt_val)
                opt_idx += 1
                
            correct_idx = int(request.POST.get(f'correct_idx_{index}', 0))
            
            if q_text and len(options) >= 2:
                if correct_idx < 0 or correct_idx >= len(options):
                    correct_idx = 0
                    
                mcq_obj = PracticeMCQQuestion.objects.create(
                    topic=topic,
                    question_text=q_text,
                    options=options,
                    correct_option_index=correct_idx,
                    explanation=explanation,
                    marks=marks,
                    difficulty=difficulty
                )
                created_mcq_ids.append(str(mcq_obj.id))
                
        elif q_type == 'CODING':
            title = request.POST.get(f'title_{index}', '').strip()
            desc = request.POST.get(f'description_{index}', '').strip()
            in_format = request.POST.get(f'input_format_{index}', '').strip()
            out_format = request.POST.get(f'output_format_{index}', '').strip()
            s_in = request.POST.get(f'sample_input_{index}', '').strip()
            s_out = request.POST.get(f'sample_output_{index}', '').strip()
            h_in = request.POST.get(f'hidden_input_{index}', '').strip()
            h_out = request.POST.get(f'hidden_output_{index}', '').strip()
            starter = request.POST.get(f'starter_code_{index}', '').strip()
            
            if title and desc:
                sample_test_cases = [{"input": s_in, "output": s_out}]
                hidden_test_cases = [{"input": h_in, "output": h_out}]
                
                coding_obj = PracticeCodingQuestion.objects.create(
                    topic=topic,
                    title=title,
                    description=desc,
                    input_format=in_format,
                    output_format=out_format,
                    sample_test_cases=sample_test_cases,
                    hidden_test_cases=hidden_test_cases,
                    starter_code=starter,
                    explanation=explanation,
                    marks=marks,
                    difficulty=difficulty
                )
                created_coding_ids.append(str(coding_obj.id))
                
        index += 1
        
    messages.success(
        request, 
        f"Bulk import completed: Created {len(created_mcq_ids)} MCQ and {len(created_coding_ids)} Coding practice questions."
    )
    
    mcq_param = ",".join(created_mcq_ids)
    coding_param = ",".join(created_coding_ids)
    return redirect(f'/dashboard/teacher/?imported_mcqs={mcq_param}&imported_codings={coding_param}#questions')
