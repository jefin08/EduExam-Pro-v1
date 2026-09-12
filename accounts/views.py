import os
import json
import random
import string
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .forms import TeacherSignUpForm, StudentSignUpForm, UserSignInForm
from .models import User, Class, Department
from content.models import Topic, TopicClassVisibility, PracticeMCQQuestion, PracticeCodingQuestion, ExamMCQQuestion, ExamCodingQuestion
from exams.models import Exam, ExamCode, OfficialGrade
from practice.models import PracticeSet, PracticeSetClassAssignment, PracticeAttempt, PracticeComment

# System Settings Storage Helper
SETTINGS_FILE = os.path.join(settings.BASE_DIR, 'system_settings.json')

def get_system_setting(key, default=None):
    if not os.path.exists(SETTINGS_FILE):
        return default
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(key, default)
    except Exception:
        return default

def set_system_setting(key, value):
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[key] = value
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

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
            
            require_approval = get_system_setting('require_user_approval', True)

            # Create teacher user
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='teacher',
                department=department,
                is_approved=not require_approval
            )
            
            if require_approval:
                messages.success(request, "Sign up request submitted successfully! Your account is pending admin approval. You will be able to sign in once an administrator approves your account.")
                return redirect('/signin/?pending=true')
            else:
                messages.success(request, "Teacher account created successfully! You can now sign in.")
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
            full_name = form.cleaned_data['full_name'].strip()
            name_parts = full_name.split(None, 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            class_group = form.cleaned_data['class_group']
            department = form.cleaned_data['department']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            require_approval = get_system_setting('require_user_approval', True)

            # Create student user
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='student',
                class_group=class_group,
                department=department,
                is_approved=not require_approval
            )
            
            if require_approval:
                messages.success(request, "Sign up request submitted successfully! Your account is pending admin approval.")
                return redirect('signin')
            else:
                messages.success(request, "Student account created successfully! You can now sign in.")
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
                # Enforce Teacher/Student approval check if approval requirement is enabled
                if user.role in ['teacher', 'student'] and not user.is_approved:
                    require_approval = get_system_setting('require_user_approval', True)
                    if require_approval:
                        messages.error(request, "Access not granted by admin. Contact admin.")
                        return redirect('signin')
                    else:
                        user.is_approved = True
                        user.save(update_fields=['is_approved'])
                
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
    
    require_user_approval = get_system_setting('require_user_approval', True)

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
        'require_user_approval': require_user_approval,
    }
    return render(request, 'dashboard/admin.html', context)

@login_required
def admin_toggle_approval_requirement(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
        
    current_status = get_system_setting('require_user_approval', True)
    new_status = not current_status
    set_system_setting('require_user_approval', new_status)
    
    if new_status:
        messages.success(request, "User registration approval requirement has been turned ON. New user registrations will require admin approval.")
    else:
        messages.success(request, "User registration approval requirement has been turned OFF. New users will be automatically approved upon registration.")
        
    return redirect('/dashboard/admin/#approval-gate-card')

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
def admin_pending_approvals_view(request):
    if request.user.role != 'admin':
        return redirect('/dashboard/admin/')
        
    pending_teachers = User.objects.filter(role='teacher', is_approved=False).order_by('-date_joined')
    pending_students = User.objects.filter(role='student', is_approved=False).select_related('class_group').order_by('-date_joined')
    
    context = {
        'pending_teachers': pending_teachers,
        'pending_students': pending_students,
        'pending_teachers_count': pending_teachers.count(),
        'pending_students_count': pending_students.count(),
        'total_pending_count': pending_teachers.count() + pending_students.count(),
    }
    return render(request, 'dashboard/admin_pending_approvals.html', context)

@login_required
def admin_users_directory_view(request):
    if request.user.role != 'admin':
        return redirect('/dashboard/admin/')
        
    teachers = User.objects.filter(role='teacher', is_approved=True).order_by('username')
    students = User.objects.filter(role='student', is_approved=True).select_related('class_group', 'class_group__department').order_by('username')
    departments = Department.objects.all().order_by('name')
    classes = Class.objects.all().select_related('department').order_by('name')
    
    # Server-side filter support
    t_search = request.GET.get('t_search', '').strip()
    t_dept = request.GET.get('t_dept', '').strip()
    if t_search:
        teachers = teachers.filter(
            Q(username__icontains=t_search) |
            Q(first_name__icontains=t_search) |
            Q(last_name__icontains=t_search) |
            Q(email__icontains=t_search)
        )
    if t_dept:
        teachers = teachers.filter(department__iexact=t_dept)
        
    s_search = request.GET.get('s_search', '').strip()
    s_class = request.GET.get('s_class', '').strip()
    s_dept = request.GET.get('s_dept', '').strip()
    if s_search:
        students = students.filter(
            Q(username__icontains=s_search) |
            Q(first_name__icontains=s_search) |
            Q(last_name__icontains=s_search) |
            Q(email__icontains=s_search)
        )
    if s_class:
        students = students.filter(class_group__name__iexact=s_class)
    if s_dept:
        students = students.filter(
            Q(class_group__department__name__iexact=s_dept) |
            Q(department__iexact=s_dept)
        )
        
    context = {
        'teachers': teachers,
        'students': students,
        'departments': departments,
        'classes': classes,
        'total_teachers': User.objects.filter(role='teacher', is_approved=True).count(),
        'total_students': User.objects.filter(role='student', is_approved=True).count(),
        't_search': t_search,
        't_dept': t_dept,
        's_search': s_search,
        's_class': s_class,
        's_dept': s_dept,
    }
    return render(request, 'dashboard/admin_users_directory.html', context)

@login_required
def admin_approve_teacher(request, teacher_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
        
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')
    teacher.is_approved = True
    teacher.save()
    messages.success(request, f"Teacher account '{teacher.username}' has been approved and activated.")
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/pending-approvals/'))

@login_required
def admin_approve_student(request, student_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
        
    student = get_object_or_404(User, id=student_id, role='student')
    student.is_approved = True
    student.save()
    messages.success(request, f"Student account '{student.username}' has been approved and activated.")
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/pending-approvals/'))

@login_required
def admin_classes_departments_view(request):
    if request.user.role != 'admin':
        return redirect('/dashboard/admin/')
        
    classes = Class.objects.all().select_related('department').order_by('name')
    departments = Department.objects.all().order_by('name')
    
    context = {
        'classes': classes,
        'departments': departments,
        'total_classes': classes.count(),
        'total_departments': departments.count(),
    }
    return render(request, 'dashboard/admin_classes_departments.html', context)

@login_required
def admin_create_class(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    class_name = request.POST.get('class_name')
    department_id = request.POST.get('department_id')
    
    department = None
    if department_id:
        department = Department.objects.filter(id=department_id).first()

    if class_name:
        Class.objects.create(
            name=class_name,
            department=department
        )
        dept_info = f" under '{department.name}'" if department else ""
        messages.success(request, f"Class '{class_name}' created successfully{dept_info}.")
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/classes-departments/'))

@login_required
def admin_onboard_users_view(request):
    if request.user.role != 'admin':
        return redirect('/dashboard/admin/')
        
    classes = Class.objects.all().select_related('department').order_by('name')
    departments = Department.objects.all().order_by('name')
    
    context = {
        'classes': classes,
        'departments': departments,
        'total_teachers': User.objects.filter(role='teacher', is_approved=True).count(),
        'total_students': User.objects.filter(role='student', is_approved=True).count(),
    }
    return render(request, 'dashboard/admin_onboard_users.html', context)

@login_required
def admin_create_teacher(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    full_name = request.POST.get('name', '').strip()
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    department = request.POST.get('department', '').strip()
    
    if not full_name:
        messages.error(request, "Full name is required.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/users/onboard/'))
        
    parts = full_name.split(None, 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    
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
                first_name=first_name,
                last_name=last_name,
                is_approved=True
            )
            messages.success(request, f"Teacher account '{username}' registered successfully.")
    else:
        messages.error(request, "Username and password are required.")
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/users/onboard/'))

@login_required
def admin_create_student(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    full_name = request.POST.get('name', '').strip()
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    class_id = request.POST.get('class_id')
    department = request.POST.get('department', '').strip()
    
    if not full_name:
        messages.error(request, "Full name is required.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/users/onboard/'))
        
    parts = full_name.split(None, 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    
    if username and password and class_id:
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
        else:
            class_group = Class.objects.filter(id=class_id).first()
            if class_group:
                if not department and class_group.department:
                    department = class_group.department.name
                User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role='student',
                    class_group=class_group,
                    department=department,
                    first_name=first_name,
                    last_name=last_name,
                    is_approved=True
                )
                messages.success(request, f"Student '{username}' enrolled in {class_group.name} successfully.")
            else:
                messages.error(request, "Selected class not found.")
    else:
        messages.error(request, "Username, password, and class are required.")
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/users/onboard/'))

def parse_student_upload_rows(file_obj, text_data):
    import csv
    import io
    import zipfile
    import xml.etree.ElementTree as ET

    rows = []
    
    # 1. Process uploaded file if provided
    if file_obj:
        fname = file_obj.name.lower()
        content_bytes = file_obj.read()
        
        if fname.endswith('.xlsx') or fname.endswith('.xls'):
            try:
                with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
                    strings = []
                    shared_xml = [n for n in z.namelist() if n.lower().endswith('sharedstrings.xml')]
                    if shared_xml:
                        tree = ET.fromstring(z.read(shared_xml[0]))
                        for elem in tree.iter():
                            if elem.tag.endswith('si'):
                                text = "".join(t.text or "" for t in elem.iter() if t.tag.endswith('t'))
                                strings.append(text)
                    
                    sheet_files = sorted([n for n in z.namelist() if 'sheet' in n.lower() and n.endswith('.xml')])
                    if sheet_files:
                        sheet_tree = ET.fromstring(z.read(sheet_files[0]))
                        for row_elem in sheet_tree.iter():
                            if row_elem.tag.endswith('row'):
                                row_data = []
                                for c in row_elem.iter():
                                    if c.tag.endswith('c'):
                                        t = c.attrib.get('t', '')
                                        val = ""
                                        v = None
                                        for child in c:
                                            if child.tag.endswith('v'):
                                                v = child.text
                                            elif child.tag.endswith('is'):
                                                val = "".join(t_elem.text or "" for t_elem in child.iter() if t_elem.tag.endswith('t'))
                                        if v is not None:
                                            if t == 's' and v.isdigit():
                                                idx = int(v)
                                                val = strings[idx] if idx < len(strings) else v
                                            else:
                                                val = v
                                        row_data.append(str(val).strip())
                                if any(row_data):
                                    rows.append(row_data)
            except Exception:
                pass
        else:
            # CSV or plain text
            try:
                text_content = content_bytes.decode('utf-8')
            except Exception:
                text_content = content_bytes.decode('latin-1', errors='replace')
            for line in text_content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '\t' in line:
                    parts = [p.strip() for p in line.split('\t')]
                elif ',' in line:
                    try:
                        parts = [p.strip() for p in next(csv.reader([line]))]
                    except Exception:
                        parts = [p.strip() for p in line.split(',')]
                elif ';' in line:
                    parts = [p.strip() for p in line.split(';')]
                elif '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                else:
                    parts = line.split()
                if parts and any(parts):
                    rows.append(parts)

    # 2. Process pasted raw text if provided
    if text_data and text_data.strip():
        import csv
        for line in text_data.strip().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '\t' in line:
                parts = [p.strip() for p in line.split('\t')]
            elif ',' in line:
                try:
                    parts = [p.strip() for p in next(csv.reader([line]))]
                except Exception:
                    parts = [p.strip() for p in line.split(',')]
            elif ';' in line:
                parts = [p.strip() for p in line.split(';')]
            elif '|' in line:
                parts = [p.strip() for p in line.split('|')]
            else:
                parts = line.split()
            if parts and any(parts):
                rows.append(parts)
                
    return rows

def extract_student_fields(row):
    """
    Extracts student fields from an uploaded row.
    Expected format: Name, Email, Registration Number, Department, Class
    Also supports: Email, Name, Registration Number, Department, Class OR Email, Reg, Dept, Class.
    """
    if not row or not any(row):
        return None
        
    cells = [str(c).strip() for c in row if c is not None]
    if not cells or not any(cells):
        return None
        
    combined = " ".join(cells).lower()
    # Detect header row
    if ('email' in combined or 'reg' in combined or 'dept' in combined or 'student' in combined or 'class' in combined) and \
       ('name' in combined or 'department' in combined or 'registration' in combined or '@' not in combined):
        return None
        
    # Find email column
    email_idx = -1
    for idx, c in enumerate(cells):
        if '@' in c and '.' in c.split('@')[-1]:
            email_idx = idx
            break
            
    if email_idx == -1:
        return None
        
    email = cells[email_idx]
    rem = [cells[i] for i in range(len(cells)) if i != email_idx]
    
    name = ''
    reg_no = ''
    dept_name = ''
    class_name = ''
    
    if email_idx == 1:
        # Standard: cells[0] is Name, cells[1] is Email
        name = cells[0]
        reg_no = rem[1] if len(rem) > 1 else ''
        dept_name = rem[2] if len(rem) > 2 else ''
        class_name = rem[3] if len(rem) > 3 else ''
    elif email_idx == 0:
        # Email first
        if len(rem) >= 4:
            name = rem[0]
            reg_no = rem[1]
            dept_name = rem[2]
            class_name = rem[3]
        elif len(rem) == 3:
            reg_no = rem[0]
            dept_name = rem[1]
            class_name = rem[2]
        elif len(rem) == 2:
            reg_no = rem[0]
            dept_name = rem[1]
        elif len(rem) == 1:
            reg_no = rem[0]
    else:
        name = cells[0]
        other_rem = [cells[i] for i in range(len(cells)) if i not in (0, email_idx)]
        reg_no = other_rem[0] if len(other_rem) > 0 else ''
        dept_name = other_rem[1] if len(other_rem) > 1 else ''
        class_name = other_rem[2] if len(other_rem) > 2 else ''
        
    username = email.split('@')[0].strip()
    if not username:
        return None
        
    password = reg_no if reg_no else username
    
    if name:
        name_parts = name.split(None, 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
    else:
        first_name = username.replace('.', ' ').replace('_', ' ').title()
        last_name = ''
        name = first_name

    return {
        'name': name,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'username': username,
        'reg_no': reg_no,
        'password': password,
        'dept_name': dept_name,
        'class_name': class_name,
    }

def enroll_single_student(s_data, dept_obj, class_obj):
    """
    Enrolls or updates a single student User record.
    Returns True if created, False if updated.
    """
    email = s_data['email']
    username = s_data['username']
    password = s_data['password']
    first_name = s_data.get('first_name', '')
    last_name = s_data.get('last_name', '')

    existing_user = User.objects.filter(Q(username=username) | Q(email=email)).first()
    if existing_user:
        existing_user.email = email
        existing_user.set_password(password)
        existing_user.role = 'student'
        if dept_obj:
            existing_user.department = dept_obj.name
        if class_obj:
            existing_user.class_group = class_obj
        existing_user.is_approved = True
        if first_name:
            existing_user.first_name = first_name
        if last_name:
            existing_user.last_name = last_name
        existing_user.save()
        return False
    else:
        final_username = username
        suffix = 1
        while User.objects.filter(username=final_username).exists():
            final_username = f"{username}_{suffix}"
            suffix += 1

        User.objects.create_user(
            username=final_username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='student',
            department=dept_obj.name if dept_obj else '',
            class_group=class_obj,
            is_approved=True
        )
        return True

@login_required
def admin_bulk_upload_students(request):
    if request.user.role != 'admin':
        return redirect('/dashboard/admin/')
        
    if request.method == 'GET':
        return render(request, 'dashboard/admin_bulk_upload.html')
        
    uploaded_file = request.FILES.get('file')
    paste_data = request.POST.get('paste_data', '')
    
    if not uploaded_file and not paste_data.strip():
        messages.error(request, "Please choose an Excel/CSV/TXT file or paste student rows to upload.")
        return redirect('admin_bulk_upload_students')
        
    raw_rows = parse_student_upload_rows(uploaded_file, paste_data)
    if not raw_rows:
        messages.error(request, "No valid student data found in the uploaded file or text.")
        return redirect('admin_bulk_upload_students')
        
    parsed_students = []
    skipped_count = 0
    
    for row in raw_rows:
        s_data = extract_student_fields(row)
        if s_data:
            parsed_students.append(s_data)
        else:
            combined = " ".join(str(c).lower() for c in row if c)
            if '@' in combined:
                skipped_count += 1
                
    if not parsed_students:
        messages.error(request, "No valid student records with email addresses could be parsed.")
        return redirect('admin_bulk_upload_students')
        
    # Verify departments and classes against existing database records
    existing_depts = {d.name.strip().lower(): d for d in Department.objects.all()}
    existing_classes = {c.name.strip().lower(): c for c in Class.objects.select_related('department').all()}
    
    has_unverified = False
    for s in parsed_students:
        d_name = s.get('dept_name', '').strip()
        c_name = s.get('class_name', '').strip()
        
        dept_match = existing_depts.get(d_name.lower()) if d_name else None
        class_match = existing_classes.get(c_name.lower()) if c_name else None
        
        s['dept_id'] = dept_match.id if dept_match else None
        s['dept_verified'] = bool(dept_match)
        s['class_id'] = class_match.id if class_match else None
        s['class_verified'] = bool(class_match)
        
        if not s['dept_verified'] or not s['class_verified']:
            has_unverified = True

    # If any department or class was NOT found, prompt admin to verify manually
    if has_unverified:
        request.session['bulk_upload_pending'] = parsed_students
        request.session['bulk_upload_skipped_count'] = skipped_count
        messages.warning(request, "Verification required: Some departments or classes in your file were not found in the system. Please verify or map them below.")
        return redirect('admin_bulk_upload_verify')

    # If all departments and classes were found, enroll directly
    created_count = 0
    updated_count = 0
    for s in parsed_students:
        dept_obj = Department.objects.filter(id=s['dept_id']).first() if s.get('dept_id') else None
        class_obj = Class.objects.filter(id=s['class_id']).first() if s.get('class_id') else None
        created = enroll_single_student(s, dept_obj, class_obj)
        if created:
            created_count += 1
        else:
            updated_count += 1

    summary_parts = []
    if created_count:
        summary_parts.append(f"{created_count} student(s) created")
    if updated_count:
        summary_parts.append(f"{updated_count} student(s) updated")
    
    msg = f"Bulk upload completed: {', '.join(summary_parts)}."
    if skipped_count:
        msg += f" ({skipped_count} row(s) skipped)."
    messages.success(request, msg)
    return redirect('/dashboard/admin/users/#students-sec')

@login_required
def admin_bulk_upload_verify(request):
    if request.user.role != 'admin':
        return redirect('/dashboard/admin/')
        
    pending_students = request.session.get('bulk_upload_pending')
    if not pending_students:
        messages.info(request, "No pending student upload requires verification.")
        return redirect('admin_bulk_upload_students')
        
    departments = Department.objects.all().order_by('name')
    classes = Class.objects.all().select_related('department').order_by('name')
    unverified_count = sum(1 for s in pending_students if not s.get('dept_verified') or not s.get('class_verified'))
    
    context = {
        'pending_students': pending_students,
        'departments': departments,
        'classes': classes,
        'unverified_count': unverified_count,
        'total_count': len(pending_students),
    }
    return render(request, 'dashboard/admin_bulk_verify.html', context)

@login_required
def admin_bulk_upload_confirm(request):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
        
    pending_students = request.session.get('bulk_upload_pending')
    if not pending_students:
        messages.error(request, "Session expired or no pending student upload found. Please upload again.")
        return redirect('/dashboard/admin/#bulk-students-sec')
        
    created_count = 0
    updated_count = 0
    
    for idx, s in enumerate(pending_students):
        # Resolve Department
        dept_val = request.POST.get(f'dept_{idx}', '').strip()
        dept_obj = None
        if dept_val.startswith('existing:'):
            dept_id = dept_val.split(':', 1)[1]
            dept_obj = Department.objects.filter(id=dept_id).first()
        elif dept_val.startswith('create:'):
            d_name = dept_val.split(':', 1)[1].strip()
            if d_name:
                dept_obj = Department.objects.filter(name__iexact=d_name).first()
                if not dept_obj:
                    dept_obj = Department.objects.create(name=d_name)
                    
        # Resolve Class
        class_val = request.POST.get(f'class_{idx}', '').strip()
        class_obj = None
        if class_val.startswith('existing:'):
            cls_id = class_val.split(':', 1)[1]
            class_obj = Class.objects.filter(id=cls_id).first()
        elif class_val.startswith('create:'):
            c_name = class_val.split(':', 1)[1].strip()
            if c_name:
                class_obj = Class.objects.filter(name__iexact=c_name).first()
                if not class_obj:
                    class_obj = Class.objects.create(name=c_name, department=dept_obj)
                elif dept_obj and not class_obj.department:
                    class_obj.department = dept_obj
                    class_obj.save()
                    
        created = enroll_single_student(s, dept_obj, class_obj)
        if created:
            created_count += 1
        else:
            updated_count += 1
            
    request.session.pop('bulk_upload_pending', None)
    request.session.pop('bulk_upload_skipped_count', None)
    
    summary_parts = []
    if created_count:
        summary_parts.append(f"{created_count} student(s) created")
    if updated_count:
        summary_parts.append(f"{updated_count} student(s) updated")
        
    messages.success(request, f"Bulk enrollment verified and completed: {', '.join(summary_parts)}.")
    return redirect('/dashboard/admin/users/#students-sec')

@login_required
def admin_bulk_upload_cancel(request):
    if request.user.role != 'admin':
        return redirect('/dashboard/admin/')
        
    request.session.pop('bulk_upload_pending', None)
    request.session.pop('bulk_upload_skipped_count', None)
    messages.info(request, "Bulk student upload was cancelled.")
    return redirect('admin_bulk_upload_students')

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
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/classes-departments/'))

@login_required
def admin_delete_class(request, class_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    class_obj = Class.objects.filter(id=class_id).first()
    if class_obj:
        name = class_obj.name
        class_obj.delete()
        messages.success(request, f"Class '{name}' deleted successfully.")
    else:
        messages.error(request, "Class not found.")
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/classes-departments/'))

@login_required
def admin_edit_class(request, class_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
        
    class_obj = Class.objects.filter(id=class_id).first()
    if not class_obj:
        messages.error(request, "Class not found.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/classes-departments/'))
        
    class_name = request.POST.get('class_name', '').strip()
    department_id = request.POST.get('department_id', '').strip()
    
    if class_name:
        duplicate = Class.objects.filter(name__iexact=class_name).exclude(id=class_id).exists()
        if duplicate:
            messages.error(request, f"Class name '{class_name}' is already taken.")
        else:
            class_obj.name = class_name
            if department_id:
                dept = Department.objects.filter(id=department_id).first()
                class_obj.department = dept
            else:
                class_obj.department = None
            class_obj.save()
            messages.success(request, f"Class '{class_name}' updated successfully.")
    else:
        messages.error(request, "Class name cannot be empty.")
        
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/classes-departments/'))

@login_required
def admin_delete_department(request, department_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    dept = Department.objects.filter(id=department_id).first()
    if dept:
        name = dept.name
        dept.delete()
        messages.success(request, f"Department '{name}' deleted successfully.")
    else:
        messages.error(request, "Department not found.")
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/classes-departments/'))

@login_required
def admin_edit_department(request, department_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
        
    dept = Department.objects.filter(id=department_id).first()
    if not dept:
        messages.error(request, "Department not found.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/classes-departments/'))
        
    dept_name = request.POST.get('department_name', '').strip()
    old_name = dept.name
    
    if dept_name:
        duplicate = Department.objects.filter(name__iexact=dept_name).exclude(id=department_id).exists()
        if duplicate:
            messages.error(request, f"Department '{dept_name}' already exists.")
        else:
            dept.name = dept_name
            dept.save()
            # Also update teachers/students if their department matched old_name
            User.objects.filter(department=old_name).update(department=dept_name)
            messages.success(request, f"Department '{dept_name}' updated successfully.")
    else:
        messages.error(request, "Department name cannot be empty.")
        
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/admin/classes-departments/'))

@login_required
def admin_delete_user(request, user_id):
    if request.user.role != 'admin' or request.method != 'POST':
        return redirect('/dashboard/admin/')
    
    user_to_delete = User.objects.filter(id=user_id).first()
    if not user_to_delete:
        messages.error(request, "User not found.")
        return redirect('/dashboard/admin/')
    
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own admin account.")
        return redirect('/dashboard/admin/')
    
    username = user_to_delete.username
    role = user_to_delete.role
    user_to_delete.delete()
    messages.success(request, f"{role.title()} '{username}' deleted successfully.")
    
    referer = request.META.get('HTTP_REFERER')
    if referer and 'pending-approvals' in referer:
        return redirect(referer)
    if role == 'teacher':
        return redirect('/dashboard/admin/#teachers-sec')
    elif role == 'student':
        return redirect('/dashboard/admin/#students-sec')
    return redirect('/dashboard/admin/')


# ----------------- TEACHER DASHBOARD & ACTIONS -----------------

@login_required
def teacher_dashboard_view(request):
    if request.user.role != 'teacher':
        return redirect_to_dashboard(request.user)
    
    teacher_dept = (request.user.department or '').strip()
    if teacher_dept:
        if teacher_dept.isdigit():
            classes = Class.objects.filter(
                Q(department__id=int(teacher_dept)) | Q(department__name__iexact=teacher_dept)
            )
        else:
            classes = Class.objects.filter(department__name__iexact=teacher_dept)
    else:
        classes = Class.objects.all()

    topics = Topic.objects.filter(teacher=request.user)
    
    raw_practice_mcqs = list(PracticeMCQQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at'))
    raw_exam_mcqs = list(ExamMCQQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at'))
    
    paired_exam_mcq_ids = set()
    display_practice_mcqs = []
    
    for pm in raw_practice_mcqs:
        matching_exam = next(
            (em for em in raw_exam_mcqs if em.id not in paired_exam_mcq_ids and em.topic_id == pm.topic_id and em.question_text.strip() == pm.question_text.strip()),
            None
        )
        if matching_exam:
            pm.is_both = True
            pm.purpose_display = 'Both'
            pm.can_copy_to_exam = False
            paired_exam_mcq_ids.add(matching_exam.id)
            pm.linked_exam_id = matching_exam.id
        else:
            pm.is_both = False
            pm.purpose_display = 'Practice'
            pm.can_copy_to_exam = True
        display_practice_mcqs.append(pm)
        
    display_exam_mcqs = [em for em in raw_exam_mcqs if em.id not in paired_exam_mcq_ids]
    for em in display_exam_mcqs:
        em.is_both = False
        em.purpose_display = 'Exam'
        em.can_copy_to_exam = False

    raw_practice_codings = list(PracticeCodingQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at'))
    raw_exam_codings = list(ExamCodingQuestion.objects.filter(topic__teacher=request.user).select_related('topic').order_by('-created_at'))
    
    paired_exam_coding_ids = set()
    display_practice_codings = []
    
    for pc in raw_practice_codings:
        matching_exam = next(
            (ec for ec in raw_exam_codings if ec.id not in paired_exam_coding_ids and ec.topic_id == pc.topic_id and ec.title.strip() == pc.title.strip()),
            None
        )
        if matching_exam:
            pc.is_both = True
            pc.purpose_display = 'Both'
            pc.can_copy_to_exam = False
            paired_exam_coding_ids.add(matching_exam.id)
            pc.linked_exam_id = matching_exam.id
        else:
            pc.is_both = False
            pc.purpose_display = 'Practice'
            pc.can_copy_to_exam = True
        display_practice_codings.append(pc)
        
    display_exam_codings = [ec for ec in raw_exam_codings if ec.id not in paired_exam_coding_ids]
    for ec in display_exam_codings:
        ec.is_both = False
        ec.purpose_display = 'Exam'
        ec.can_copy_to_exam = False

    practice_sets = PracticeSet.objects.filter(teacher=request.user).prefetch_related('assignments__class_group', 'topics')
    exams = Exam.objects.filter(teacher=request.user).prefetch_related('codes__class_group', 'topics')
    all_official_grades = OfficialGrade.objects.filter(exam__teacher=request.user).select_related('student', 'student__class_group', 'exam').order_by('-submitted_at')
    
    context = {
        'classes': classes,
        'topics': topics,
        'practice_mcqs': display_practice_mcqs,
        'exam_mcqs': display_exam_mcqs,
        'practice_coding_qs': display_practice_codings,
        'exam_coding_qs': display_exam_codings,
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
            class_group = Class.objects.filter(id=class_id).first()
            if class_group:
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
    
    q_type = request.GET.get('type') or request.POST.get('question_type')
    
    if topic_id and question_text and opt1 and opt2 and correct_idx is not None:
        topic = get_object_or_404(Topic, id=topic_id, teacher=request.user)
        options = [opt1, opt2]
        if opt3: options.append(opt3)
        if opt4: options.append(opt4)
        
        # Check if question should be saved for both, exam, or practice
        target_mode = q_type if q_type in ['both', 'exam', 'practice'] else topic.purpose
        
        if target_mode == 'both':
            PracticeMCQQuestion.objects.create(
                topic=topic,
                question_text=question_text,
                options=options,
                correct_option_index=int(correct_idx),
                marks=int(marks),
                difficulty=difficulty,
                explanation=explanation
            )
            ExamMCQQuestion.objects.create(
                topic=topic,
                question_text=question_text,
                options=options,
                correct_option_index=int(correct_idx),
                marks=int(marks),
                difficulty=difficulty,
                explanation=explanation
            )
            messages.success(request, f"Multiple-choice question added to BOTH Exam and Practice for topic '{topic.name}'.")
        elif target_mode == 'exam':
            ExamMCQQuestion.objects.create(
                topic=topic,
                question_text=question_text,
                options=options,
                correct_option_index=int(correct_idx),
                marks=int(marks),
                difficulty=difficulty,
                explanation=explanation
            )
            messages.success(request, f"Exam multiple-choice question added for topic '{topic.name}'.")
        else:
            PracticeMCQQuestion.objects.create(
                topic=topic,
                question_text=question_text,
                options=options,
                correct_option_index=int(correct_idx),
                marks=int(marks),
                difficulty=difficulty,
                explanation=explanation
            )
            messages.success(request, f"Practice multiple-choice question added for topic '{topic.name}'.")
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
    
    # Support multiple sample test cases
    sample_inputs = request.POST.getlist('sample_inputs[]')
    sample_outputs = request.POST.getlist('sample_outputs[]')
    sample_cases = []
    for inp, out in zip(sample_inputs, sample_outputs):
        if inp.strip() or out.strip():
            sample_cases.append({'input': inp.strip(), 'output': out.strip()})
    if not sample_cases:
        s_in = request.POST.get('sample_input', '').strip()
        s_out = request.POST.get('sample_output', '').strip()
        if s_in or s_out:
            sample_cases.append({'input': s_in, 'output': s_out})

    # Support multiple hidden test cases
    hidden_inputs = request.POST.getlist('hidden_inputs[]')
    hidden_outputs = request.POST.getlist('hidden_outputs[]')
    hidden_cases = []
    for inp, out in zip(hidden_inputs, hidden_outputs):
        if inp.strip() or out.strip():
            hidden_cases.append({'input': inp.strip(), 'output': out.strip()})
    if not hidden_cases:
        h_in = request.POST.get('hidden_input', '').strip()
        h_out = request.POST.get('hidden_output', '').strip()
        if h_in or h_out:
            hidden_cases.append({'input': h_in, 'output': h_out})
        elif sample_cases:
            hidden_cases = list(sample_cases)

    starter_code = request.POST.get('starter_code', '')
    time_limit = request.POST.get('time_limit', 2)
    memory_limit = request.POST.get('memory_limit', 256)
    marks = request.POST.get('marks', 5)
    difficulty = request.POST.get('difficulty', 'medium')
    explanation = request.POST.get('explanation', '')
    
    q_type = request.GET.get('type') or request.POST.get('question_type')

    if topic_id and title and description and sample_cases:
        topic = get_object_or_404(Topic, id=topic_id, teacher=request.user)
        
        t_limit = int(time_limit) if str(time_limit).isdigit() else 2
        m_limit = int(memory_limit) if str(memory_limit).isdigit() else 256
        m_marks = int(marks) if str(marks).isdigit() else 5
        
        target_mode = q_type if q_type in ['both', 'exam', 'practice'] else topic.purpose
        
        if target_mode == 'both':
            PracticeCodingQuestion.objects.create(
                topic=topic,
                title=title,
                description=description,
                input_format=input_format,
                output_format=output_format,
                sample_test_cases=sample_cases,
                hidden_test_cases=hidden_cases,
                starter_code=starter_code,
                time_limit=t_limit,
                memory_limit=m_limit,
                marks=m_marks,
                difficulty=difficulty,
                explanation=explanation
            )
            ExamCodingQuestion.objects.create(
                topic=topic,
                title=title,
                description=description,
                input_format=input_format,
                output_format=output_format,
                sample_test_cases=sample_cases,
                hidden_test_cases=hidden_cases,
                starter_code=starter_code,
                time_limit=t_limit,
                memory_limit=m_limit,
                marks=m_marks,
                difficulty=difficulty
            )
            messages.success(request, f"Coding question '{title}' added to BOTH Exam and Practice for topic '{topic.name}'.")
        elif target_mode == 'exam':
            ExamCodingQuestion.objects.create(
                topic=topic,
                title=title,
                description=description,
                input_format=input_format,
                output_format=output_format,
                sample_test_cases=sample_cases,
                hidden_test_cases=hidden_cases,
                starter_code=starter_code,
                time_limit=t_limit,
                memory_limit=m_limit,
                marks=m_marks,
                difficulty=difficulty
            )
            messages.success(request, f"Exam coding question '{title}' added for topic '{topic.name}'.")
        else:
            PracticeCodingQuestion.objects.create(
                topic=topic,
                title=title,
                description=description,
                input_format=input_format,
                output_format=output_format,
                sample_test_cases=sample_cases,
                hidden_test_cases=hidden_cases,
                starter_code=starter_code,
                time_limit=t_limit,
                memory_limit=m_limit,
                marks=m_marks,
                difficulty=difficulty,
                explanation=explanation
            )
            messages.success(request, f"Practice coding question '{title}' added for topic '{topic.name}'.")
    return redirect('/dashboard/teacher/#questions')

@login_required
def teacher_create_practice(request):
    if request.user.role != 'teacher' or request.method != 'POST':
        return redirect('/dashboard/teacher/')
    
    name = request.POST.get('name')
    topic_ids = request.POST.getlist('topic_ids')
    class_ids = request.POST.getlist('class_ids')
    is_randomized = request.POST.get('is_randomized') in ['true', 'True', '1', 'on']
    
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
            solution_reveal_rule='immediate',
            is_randomized=is_randomized
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
    is_randomized = request.POST.get('is_randomized') in ['true', 'True', '1', 'on']
    
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
            end_time=aware_end,
            is_randomized=is_randomized
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

def get_student_exam_grades(student):
    now = timezone.now()
    class_group = student.class_group
    from datetime import timedelta

    existing_grades = list(
        OfficialGrade.objects.filter(student=student)
        .select_related('exam')
        .order_by('-submitted_at')
    )

    graded_exam_ids = set()
    result_list = []

    for g in existing_grades:
        graded_exam_ids.add(g.exam_id)
        if g.is_submitted:
            result_list.append({
                'exam': g.exam,
                'score': round(g.score, 1),
                'submitted_at': g.submitted_at,
                'is_absent': False,
                'status': 'Completed',
                'sort_date': g.submitted_at or g.started_at or g.exam.end_time,
            })
        else:
            # Started/entered but never submitted; if exam ended or late deadline passed
            if now > g.exam.end_time or now > (g.exam.start_time + timedelta(minutes=15)):
                result_list.append({
                    'exam': g.exam,
                    'score': 0,
                    'submitted_at': g.exam.end_time,
                    'is_absent': True,
                    'status': 'Absent',
                    'sort_date': g.exam.end_time,
                })

    # Exams assigned to the student's class group that the student never entered
    if class_group:
        assigned_exams = list(
            Exam.objects.filter(codes__class_group=class_group)
            .exclude(id__in=graded_exam_ids)
            .distinct()
            .order_by('-start_time')
        )
        for exam in assigned_exams:
            if now > exam.end_time or now > (exam.start_time + timedelta(minutes=15)):
                result_list.append({
                    'exam': exam,
                    'score': 0,
                    'submitted_at': exam.end_time,
                    'is_absent': True,
                    'status': 'Absent',
                    'sort_date': exam.end_time,
                })

    result_list.sort(key=lambda x: x['sort_date'] if x['sort_date'] else now, reverse=True)
    return result_list

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
    
    official_grades = get_student_exam_grades(request.user)
    
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
    
    topics_count = Topic.objects.filter(teacher=request.user).count()
    practice_sets_count = PracticeSet.objects.filter(teacher=request.user).count()
    exams_count = Exam.objects.filter(teacher=request.user).count()
    
    practice_mcq_count = PracticeMCQQuestion.objects.filter(topic__teacher=request.user).count()
    practice_coding_count = PracticeCodingQuestion.objects.filter(topic__teacher=request.user).count()
    exam_mcq_count = ExamMCQQuestion.objects.filter(topic__teacher=request.user).count()
    exam_coding_count = ExamCodingQuestion.objects.filter(topic__teacher=request.user).count()
    total_questions_count = practice_mcq_count + practice_coding_count + exam_mcq_count + exam_coding_count

    context = {
        'teacher': request.user,
        'topics_count': topics_count,
        'practice_sets_count': practice_sets_count,
        'exams_count': exams_count,
        'total_questions_count': total_questions_count,
    }
    return render(request, 'dashboard/teacher_profile.html', context)

@login_required
def teacher_students_progress_view(request):
    if request.user.role != 'teacher':
        return redirect_to_dashboard(request.user)

    teacher_dept = (request.user.department or '').strip()
    if teacher_dept:
        if teacher_dept.isdigit():
            classes = Class.objects.filter(
                Q(department__id=int(teacher_dept)) | Q(department__name__iexact=teacher_dept)
            )
        else:
            classes = Class.objects.filter(department__name__iexact=teacher_dept)
    else:
        classes = Class.objects.all()

    # Also include any classes that have exams assigned by this teacher
    exam_class_ids = ExamCode.objects.filter(exam__teacher=request.user, class_group__isnull=False).values_list('class_group_id', flat=True)
    classes = (classes | Class.objects.filter(id__in=exam_class_ids)).distinct().order_by('name')

    selected_class_id = request.GET.get('class_id', '').strip()
    selected_class = None
    students_data = []
    class_stats = {
        'total_students': 0,
        'overall_attendance_pct': 0,
        'overall_avg_score': 0,
        'total_attended': 0,
        'total_absent': 0,
    }

    now = timezone.now()

    if selected_class_id and selected_class_id.isdigit():
        selected_class = classes.filter(id=int(selected_class_id)).first()

    if selected_class:
        students = list(User.objects.filter(role='student', class_group=selected_class).order_by('first_name', 'last_name', 'username'))
        
        # Teacher's exams scheduled for this class
        teacher_exams = list(
            Exam.objects.filter(
                teacher=request.user,
                codes__class_group=selected_class
            ).distinct().order_by('-start_time')
        )

        all_scores = []
        all_attended_count = 0
        all_absent_count = 0

        # Pre-fetch all grades for these students across this teacher's exams
        exam_ids = [e.id for e in teacher_exams]
        grades = list(
            OfficialGrade.objects.filter(
                student__in=students,
                exam_id__in=exam_ids
            ).select_related('exam')
        )
        grades_map = {}
        for g in grades:
            if g.student_id not in grades_map:
                grades_map[g.student_id] = {}
            grades_map[g.student_id][g.exam_id] = g

        for student in students:
            student_grades = grades_map.get(student.id, {})
            attended_list = []
            absent_list = []
            student_scores = []

            for exam in teacher_exams:
                grade = student_grades.get(exam.id)
                if grade and (grade.is_submitted or grade.score > 0 or grade.started_at):
                    score_val = round(grade.score, 1)
                    student_scores.append(score_val)
                    all_scores.append(score_val)
                    attended_list.append({
                        'exam': exam,
                        'score': score_val,
                        'mcq_score': round(grade.mcq_score, 1),
                        'coding_score': round(grade.coding_score, 1),
                        'submitted_at': grade.submitted_at or grade.started_at,
                        'is_submitted': grade.is_submitted,
                    })
                elif exam.end_time < now:
                    absent_list.append({
                        'exam': exam,
                        'start_time': exam.start_time,
                        'end_time': exam.end_time,
                        'duration_minutes': exam.duration_minutes,
                    })

            attended_count = len(attended_list)
            absent_count = len(absent_list)
            total_eval = attended_count + absent_count
            all_attended_count += attended_count
            all_absent_count += absent_count

            attendance_pct = round((attended_count / total_eval * 100), 1) if total_eval > 0 else (100.0 if not absent_list else 0.0)
            avg_score = round(sum(student_scores) / len(student_scores), 1) if student_scores else 0.0
            max_score = max(student_scores) if student_scores else 0.0
            min_score = min(student_scores) if student_scores else 0.0

            if not attended_list and not absent_list:
                perf_badge = 'No Exams'
                perf_color = 'var(--ink-soft)'
                summary_note = 'No scheduled exams have concluded for this class yet.'
            elif avg_score >= 80:
                perf_badge = 'Excellent'
                perf_color = 'var(--pass-teal)'
                summary_note = f'Outstanding performance with an average score of {avg_score}%. Strong participation and mastery across assessments.'
            elif avg_score >= 60:
                perf_badge = 'Good'
                perf_color = '#3b82f6'
                summary_note = f'Consistent academic progress with an average score of {avg_score}%. Regular attendance across exams.'
            elif avg_score >= 40:
                perf_badge = 'Average'
                perf_color = '#f59e0b'
                summary_note = f'Moderate performance with an average score of {avg_score}%. Would benefit from targeted practice to improve.'
            else:
                perf_badge = 'Needs Attention'
                perf_color = 'var(--red-pen)'
                summary_note = f'Average score is {avg_score}% with {absent_count} missed exam(s). Requires academic follow-up and remediation.'

            students_data.append({
                'student': student,
                'attended_exams': attended_list,
                'absent_exams': absent_list,
                'attended_count': attended_count,
                'absent_count': absent_count,
                'attendance_pct': attendance_pct,
                'avg_score': avg_score,
                'max_score': max_score,
                'min_score': min_score,
                'perf_badge': perf_badge,
                'perf_color': perf_color,
                'summary_note': summary_note,
            })

        class_stats['total_students'] = len(students)
        class_stats['total_attended'] = all_attended_count
        class_stats['total_absent'] = all_absent_count
        total_class_eval = all_attended_count + all_absent_count
        class_stats['overall_attendance_pct'] = round((all_attended_count / total_class_eval * 100), 1) if total_class_eval > 0 else 0.0
        class_stats['overall_avg_score'] = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_class_id': selected_class.id if selected_class else '',
        'students_data': students_data,
        'class_stats': class_stats,
    }
    return render(request, 'dashboard/teacher_students_progress.html', context)
    

@login_required
def teacher_practice_comments_view(request):
    if request.user.role not in ['teacher', 'admin']:
        return redirect_to_dashboard(request.user)

    teacher_dept = (request.user.department or '').strip()
    if teacher_dept:
        if teacher_dept.isdigit():
            classes = Class.objects.filter(
                Q(department__id=int(teacher_dept)) | Q(department__name__iexact=teacher_dept)
            )
        else:
            classes = Class.objects.filter(department__name__iexact=teacher_dept)
    else:
        classes = Class.objects.all()
    classes = classes.order_by('name')

    selected_class_id = request.GET.get('class_id', '').strip()
    selected_question = request.GET.get('question', '').strip()
    view_mode = request.GET.get('view_mode', 'by_question').strip()
    search_query = request.GET.get('q', '').strip()

    comments_qs = PracticeComment.objects.select_related(
        'student', 'student__class_group', 'student__class_group__department',
        'mcq_question', 'mcq_question__topic',
        'coding_question', 'coding_question__topic'
    ).order_by('-created_at')

    # Restrict comments and question filter to questions added by the requesting teacher
    if request.user.role == 'teacher':
        comments_qs = comments_qs.filter(
            Q(mcq_question__topic__teacher=request.user) | Q(coding_question__topic__teacher=request.user)
        )
        commented_mcq_ids = PracticeComment.objects.filter(
            question_type='mcq', mcq_question__isnull=False, mcq_question__topic__teacher=request.user
        ).values_list('mcq_question_id', flat=True).distinct()
        commented_coding_ids = PracticeComment.objects.filter(
            question_type='coding', coding_question__isnull=False, coding_question__topic__teacher=request.user
        ).values_list('coding_question_id', flat=True).distinct()

        mcq_filter_options = PracticeMCQQuestion.objects.filter(
            id__in=commented_mcq_ids, topic__teacher=request.user
        ).select_related('topic').order_by('topic__name', 'id')
        coding_filter_options = PracticeCodingQuestion.objects.filter(
            id__in=commented_coding_ids, topic__teacher=request.user
        ).select_related('topic').order_by('topic__name', 'title')
    else:
        commented_mcq_ids = PracticeComment.objects.filter(
            question_type='mcq', mcq_question__isnull=False
        ).values_list('mcq_question_id', flat=True).distinct()
        commented_coding_ids = PracticeComment.objects.filter(
            question_type='coding', coding_question__isnull=False
        ).values_list('coding_question_id', flat=True).distinct()

        mcq_filter_options = PracticeMCQQuestion.objects.filter(
            id__in=commented_mcq_ids
        ).select_related('topic').order_by('topic__name', 'id')
        coding_filter_options = PracticeCodingQuestion.objects.filter(
            id__in=commented_coding_ids
        ).select_related('topic').order_by('topic__name', 'title')

    if selected_class_id and selected_class_id.isdigit():
        comments_qs = comments_qs.filter(student__class_group_id=int(selected_class_id))

    if selected_question:
        if selected_question.startswith('mcq_'):
            q_id = selected_question.split('_')[1]
            if q_id.isdigit():
                comments_qs = comments_qs.filter(question_type='mcq', mcq_question_id=int(q_id))
        elif selected_question.startswith('coding_'):
            q_id = selected_question.split('_')[1]
            if q_id.isdigit():
                comments_qs = comments_qs.filter(question_type='coding', coding_question_id=int(q_id))

    if search_query:
        comments_qs = comments_qs.filter(
            Q(comment_text__icontains=search_query) |
            Q(student__username__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(mcq_question__question_text__icontains=search_query) |
            Q(coding_question__title__icontains=search_query)
        )

    # Group comments by question for "Group by Question" view
    grouped_dict = {}
    for comment in comments_qs:
        if comment.question_type == 'mcq' and comment.mcq_question:
            key = ('mcq', comment.mcq_question.id)
            if key not in grouped_dict:
                grouped_dict[key] = {
                    'question_type': 'mcq',
                    'question_id': comment.mcq_question.id,
                    'question_key': f"mcq_{comment.mcq_question.id}",
                    'topic': comment.mcq_question.topic,
                    'text': comment.mcq_question.question_text,
                    'explanation': comment.mcq_question.explanation,
                    'comments': [],
                }
            grouped_dict[key]['comments'].append(comment)
        elif comment.question_type == 'coding' and comment.coding_question:
            key = ('coding', comment.coding_question.id)
            if key not in grouped_dict:
                grouped_dict[key] = {
                    'question_type': 'coding',
                    'question_id': comment.coding_question.id,
                    'question_key': f"coding_{comment.coding_question.id}",
                    'topic': comment.coding_question.topic,
                    'text': comment.coding_question.title,
                    'description': comment.coding_question.description,
                    'explanation': comment.coding_question.explanation,
                    'comments': [],
                }
            grouped_dict[key]['comments'].append(comment)

    questions_grouped = list(grouped_dict.values())

    context = {
        'comments': comments_qs,
        'questions_grouped': questions_grouped,
        'classes': classes,
        'selected_class_id': selected_class_id,
        'selected_question': selected_question,
        'mcq_filter_options': mcq_filter_options,
        'coding_filter_options': coding_filter_options,
        'view_mode': view_mode,
        'search_query': search_query,
        'total_comments': comments_qs.count(),
        'total_questions_with_comments': len(questions_grouped),
    }
    return render(request, 'dashboard/teacher_practice_comments.html', context)



@login_required
def teacher_delete_practice_comment(request, comment_id):
    if request.user.role not in ['teacher', 'admin'] or request.method != 'POST':
        return redirect_to_dashboard(request.user)

    comment = get_object_or_404(PracticeComment, id=comment_id)
    if request.user.role == 'teacher':
        is_mcq_owner = comment.mcq_question and comment.mcq_question.topic and comment.mcq_question.topic.teacher == request.user
        is_coding_owner = comment.coding_question and comment.coding_question.topic and comment.coding_question.topic.teacher == request.user
        if not (is_mcq_owner or is_coding_owner):
            messages.error(request, "You can only delete comments on questions you created.")
            return redirect(request.META.get('HTTP_REFERER', 'teacher_practice_comments'))

    student_name = comment.student.get_full_name() or comment.student.username
    comment.delete()
    messages.success(request, f"Practice comment by {student_name} deleted successfully.")

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('teacher_practice_comments')


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
    q_text = question.question_text
    
    TwinModel = PracticeMCQQuestion if q_type == 'exam' else ExamMCQQuestion
    TwinModel.objects.filter(topic_id=topic_id, question_text=q_text).delete()
    
    question.delete()
    messages.success(request, "Multiple-choice question deleted successfully.")
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
    
    TwinModel = PracticeCodingQuestion if q_type == 'exam' else ExamCodingQuestion
    TwinModel.objects.filter(topic_id=topic_id, title=title).delete()
    
    question.delete()
    messages.success(request, f"Coding question '{title}' deleted successfully.")
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
        old_text = question.question_text
        old_topic = question.topic
        
        # Topic edit
        new_topic_id = request.POST.get('topic_id')
        if new_topic_id:
            new_topic = Topic.objects.filter(id=new_topic_id, teacher=request.user).first()
            if new_topic:
                question.topic = new_topic
        
        question.question_text = request.POST.get('question_text')
        
        opt1 = request.POST.get('option_0')
        opt2 = request.POST.get('option_1')
        opt3 = request.POST.get('option_2')
        opt4 = request.POST.get('option_3')
        
        options = [opt1, opt2]
        if opt3 and opt3.strip(): options.append(opt3.strip())
        if opt4 and opt4.strip(): options.append(opt4.strip())
        
        question.options = options
        question.correct_option_index = int(request.POST.get('correct_option_index', 0))
        question.marks = int(request.POST.get('marks', 1))
        question.difficulty = request.POST.get('difficulty', 'medium')
        question.explanation = request.POST.get('explanation', '')
        
        question.save()

        # Existing twin check
        TwinModel = ExamMCQQuestion if q_type == 'practice' else PracticeMCQQuestion
        twin = TwinModel.objects.filter(topic=old_topic, question_text=old_text).first()
        
        # Purpose edit: 'both', 'practice', 'exam'
        target_purpose = request.POST.get('purpose')
        if target_purpose:
            if target_purpose == 'both':
                if twin:
                    twin.topic = question.topic
                    twin.question_text = question.question_text
                    twin.options = question.options
                    twin.correct_option_index = question.correct_option_index
                    twin.marks = question.marks
                    twin.difficulty = question.difficulty
                    twin.explanation = question.explanation
                    twin.save()
                else:
                    TwinModel.objects.create(
                        topic=question.topic,
                        question_text=question.question_text,
                        options=question.options,
                        correct_option_index=question.correct_option_index,
                        marks=question.marks,
                        difficulty=question.difficulty,
                        explanation=question.explanation
                    )
            elif target_purpose == 'practice':
                if q_type == 'exam':
                    PracticeMCQQuestion.objects.create(
                        topic=question.topic,
                        question_text=question.question_text,
                        options=question.options,
                        correct_option_index=question.correct_option_index,
                        marks=question.marks,
                        difficulty=question.difficulty,
                        explanation=question.explanation
                    )
                    question.delete()
                elif twin:
                    twin.delete()
            elif target_purpose == 'exam':
                if q_type == 'practice':
                    ExamMCQQuestion.objects.create(
                        topic=question.topic,
                        question_text=question.question_text,
                        options=question.options,
                        correct_option_index=question.correct_option_index,
                        marks=question.marks,
                        difficulty=question.difficulty,
                        explanation=question.explanation
                    )
                    question.delete()
                elif twin:
                    twin.delete()
        elif twin:
            twin.topic = question.topic
            twin.question_text = question.question_text
            twin.options = question.options
            twin.correct_option_index = question.correct_option_index
            twin.marks = question.marks
            twin.difficulty = question.difficulty
            twin.explanation = question.explanation
            twin.save()

        messages.success(request, "Multiple-choice question updated successfully.")
        return redirect('/dashboard/teacher/#questions')
        
    topics = Topic.objects.filter(teacher=request.user)
    TwinModel = ExamMCQQuestion if q_type == 'practice' else PracticeMCQQuestion
    is_both = TwinModel.objects.filter(topic=question.topic, question_text=question.question_text).exists()
    return render(request, 'dashboard/teacher_edit_mcq.html', {
        'question': question,
        'q_type': q_type,
        'topics': topics,
        'is_both': is_both,
    })

@login_required
def teacher_edit_coding(request, question_id):
    if request.user.role != 'teacher':
        return redirect('/dashboard/teacher/')
        
    q_type = request.GET.get('type', 'practice')
    ModelClass = ExamCodingQuestion if q_type == 'exam' else PracticeCodingQuestion
    question = get_object_or_404(ModelClass, id=question_id, topic__teacher=request.user)
    
    if request.method == 'POST':
        old_title = question.title
        old_topic = question.topic
        
        # Topic edit
        new_topic_id = request.POST.get('topic_id')
        if new_topic_id:
            new_topic = Topic.objects.filter(id=new_topic_id, teacher=request.user).first()
            if new_topic:
                question.topic = new_topic
                
        question.title = request.POST.get('title')
        question.description = request.POST.get('description')
        question.input_format = request.POST.get('input_format')
        question.output_format = request.POST.get('output_format')
        
        sample_inputs = request.POST.getlist('sample_inputs[]')
        sample_outputs = request.POST.getlist('sample_outputs[]')
        sample_cases = []
        for inp, out in zip(sample_inputs, sample_outputs):
            if inp.strip() or out.strip():
                sample_cases.append({'input': inp.strip(), 'output': out.strip()})
        if not sample_cases:
            s_in = request.POST.get('sample_input', '').strip()
            s_out = request.POST.get('sample_output', '').strip()
            if s_in or s_out:
                sample_cases.append({'input': s_in, 'output': s_out})

        hidden_inputs = request.POST.getlist('hidden_inputs[]')
        hidden_outputs = request.POST.getlist('hidden_outputs[]')
        hidden_cases = []
        for inp, out in zip(hidden_inputs, hidden_outputs):
            if inp.strip() or out.strip():
                hidden_cases.append({'input': inp.strip(), 'output': out.strip()})
        if not hidden_cases:
            h_in = request.POST.get('hidden_input', '').strip()
            h_out = request.POST.get('hidden_output', '').strip()
            if h_in or h_out:
                hidden_cases.append({'input': h_in, 'output': h_out})
            elif sample_cases:
                hidden_cases = list(sample_cases)
        
        question.sample_test_cases = sample_cases
        question.hidden_test_cases = hidden_cases
        
        question.starter_code = request.POST.get('starter_code', '')
        time_lim = request.POST.get('time_limit', 2)
        mem_lim = request.POST.get('memory_limit', 256)
        question.time_limit = int(time_lim) if str(time_lim).isdigit() else 2
        question.memory_limit = int(mem_lim) if str(mem_lim).isdigit() else 256
        
        question.marks = int(request.POST.get('marks', 5))
        question.difficulty = request.POST.get('difficulty', 'medium')
        
        if hasattr(question, 'explanation') or 'explanation' in request.POST:
            question.explanation = request.POST.get('explanation', '')
        
        question.save()

        # Existing twin check
        TwinModel = ExamCodingQuestion if q_type == 'practice' else PracticeCodingQuestion
        twin = TwinModel.objects.filter(topic=old_topic, title=old_title).first()
        
        # Purpose edit: 'both', 'practice', 'exam'
        target_purpose = request.POST.get('purpose')
        if target_purpose:
            if target_purpose == 'both':
                if twin:
                    twin.topic = question.topic
                    twin.title = question.title
                    twin.description = question.description
                    twin.input_format = question.input_format
                    twin.output_format = question.output_format
                    twin.sample_test_cases = question.sample_test_cases
                    twin.hidden_test_cases = question.hidden_test_cases
                    twin.starter_code = question.starter_code
                    twin.time_limit = question.time_limit
                    twin.memory_limit = question.memory_limit
                    twin.marks = question.marks
                    twin.difficulty = question.difficulty
                    if hasattr(twin, 'explanation'):
                        twin.explanation = getattr(question, 'explanation', '')
                    twin.save()
                else:
                    TwinModel.objects.create(
                        topic=question.topic,
                        title=question.title,
                        description=question.description,
                        input_format=question.input_format,
                        output_format=question.output_format,
                        sample_test_cases=question.sample_test_cases,
                        hidden_test_cases=question.hidden_test_cases,
                        starter_code=question.starter_code,
                        time_limit=question.time_limit,
                        memory_limit=question.memory_limit,
                        marks=question.marks,
                        difficulty=question.difficulty,
                        explanation=getattr(question, 'explanation', '')
                    )
            elif target_purpose == 'practice':
                if q_type == 'exam':
                    PracticeCodingQuestion.objects.create(
                        topic=question.topic,
                        title=question.title,
                        description=question.description,
                        input_format=question.input_format,
                        output_format=question.output_format,
                        sample_test_cases=question.sample_test_cases,
                        hidden_test_cases=question.hidden_test_cases,
                        starter_code=question.starter_code,
                        time_limit=question.time_limit,
                        memory_limit=question.memory_limit,
                        marks=question.marks,
                        difficulty=question.difficulty,
                        explanation=getattr(question, 'explanation', '')
                    )
                    question.delete()
                elif twin:
                    twin.delete()
            elif target_purpose == 'exam':
                if q_type == 'practice':
                    ExamCodingQuestion.objects.create(
                        topic=question.topic,
                        title=question.title,
                        description=question.description,
                        input_format=question.input_format,
                        output_format=question.output_format,
                        sample_test_cases=question.sample_test_cases,
                        hidden_test_cases=question.hidden_test_cases,
                        starter_code=question.starter_code,
                        time_limit=question.time_limit,
                        memory_limit=question.memory_limit,
                        marks=question.marks,
                        difficulty=question.difficulty,
                        explanation=getattr(question, 'explanation', '')
                    )
                    question.delete()
                elif twin:
                    twin.delete()
        elif twin:
            twin.topic = question.topic
            twin.title = question.title
            twin.description = question.description
            twin.input_format = question.input_format
            twin.output_format = question.output_format
            twin.sample_test_cases = question.sample_test_cases
            twin.hidden_test_cases = question.hidden_test_cases
            twin.starter_code = question.starter_code
            twin.time_limit = question.time_limit
            twin.memory_limit = question.memory_limit
            twin.marks = question.marks
            twin.difficulty = question.difficulty
            if hasattr(twin, 'explanation'):
                twin.explanation = getattr(question, 'explanation', '')
            twin.save()

        messages.success(request, f"Coding question '{question.title}' updated successfully.")
        return redirect('/dashboard/teacher/#questions')
        
    topics = Topic.objects.filter(teacher=request.user)
    TwinModel = ExamCodingQuestion if q_type == 'practice' else PracticeCodingQuestion
    is_both = TwinModel.objects.filter(topic=question.topic, title=question.title).exists()
    return render(request, 'dashboard/teacher_edit_coding.html', {
        'question': question,
        'q_type': q_type,
        'topics': topics,
        'is_both': is_both,
    })


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
        sample_cases = []
        hidden_cases = []
        cur_sample_in = ""
        cur_sample_out = ""
        cur_hidden_in = ""
        cur_hidden_out = ""
        starter_code = ""
        
        # Read line by line
        current_multiline_field = None
        multiline_buffer = []
        
        def flush_multiline():
            nonlocal current_multiline_field, multiline_buffer, q_text, description, input_format, output_format
            nonlocal sample_cases, hidden_cases, cur_sample_in, cur_sample_out, cur_hidden_in, cur_hidden_out, starter_code, explanation
            val = "\n".join(multiline_buffer).strip()
            if not val:
                multiline_buffer = []
                current_multiline_field = None
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
                cur_sample_in = val
            elif current_multiline_field == 'sample_output':
                cur_sample_out = val
                sample_cases.append({'input': cur_sample_in, 'output': cur_sample_out})
                cur_sample_in = ""
                cur_sample_out = ""
            elif current_multiline_field == 'hidden_input':
                cur_hidden_in = val
            elif current_multiline_field == 'hidden_output':
                cur_hidden_out = val
                hidden_cases.append({'input': cur_hidden_in, 'output': cur_hidden_out})
                cur_hidden_in = ""
                cur_hidden_out = ""
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
                
            elif re.match(r'^sample\s+input(\s*#?\d+)?:', lower_line):
                flush_multiline()
                current_multiline_field = 'sample_input'
                idx_pos = line_str.find(':')
                multiline_buffer.append(line_str[idx_pos + 1:].strip())
                
            elif re.match(r'^sample\s+output(\s*#?\d+)?:', lower_line):
                flush_multiline()
                current_multiline_field = 'sample_output'
                idx_pos = line_str.find(':')
                multiline_buffer.append(line_str[idx_pos + 1:].strip())
                
            elif re.match(r'^hidden\s+input(\s*#?\d+)?:', lower_line):
                flush_multiline()
                current_multiline_field = 'hidden_input'
                idx_pos = line_str.find(':')
                multiline_buffer.append(line_str[idx_pos + 1:].strip())
                
            elif re.match(r'^hidden\s+output(\s*#?\d+)?:', lower_line):
                flush_multiline()
                current_multiline_field = 'hidden_output'
                idx_pos = line_str.find(':')
                multiline_buffer.append(line_str[idx_pos + 1:].strip())
                
            elif lower_line.startswith('starter code:'):
                flush_multiline()
                current_multiline_field = 'starter_code'
                multiline_buffer.append(line_str[13:].strip())
                
            # Options: supports "Option A:", "Option A)", "A)", "A.", "A:"
            elif re.match(r'^(?:option\s+)?([A-Z])[\)\.:]\s*(.*)$', line_str, re.IGNORECASE):
                flush_multiline()
                opt_match = re.match(r'^(?:option\s+)?([A-Z])[\)\.:]\s*(.*)$', line_str, re.IGNORECASE)
                if opt_match:
                    opt_letter = opt_match.group(1).upper()
                    opt_text = opt_match.group(2).strip()
                    options.append((opt_letter, opt_text))
            
            # If we are inside a multiline field, continue appending
            elif current_multiline_field:
                multiline_buffer.append(line)
                
        flush_multiline()
        if cur_sample_in or cur_sample_out:
            sample_cases.append({'input': cur_sample_in, 'output': cur_sample_out})
        if cur_hidden_in or cur_hidden_out:
            hidden_cases.append({'input': cur_hidden_in, 'output': cur_hidden_out})
        
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
            if not sample_cases:
                warnings.append("Missing Sample Test Cases.")
            if not hidden_cases:
                if sample_cases:
                    hidden_cases = [{'input': sc['input'], 'output': sc['output']} for sc in sample_cases]
                else:
                    warnings.append("Missing Hidden Test Cases.")
                
            parsed_questions.append({
                'type': 'CODING',
                'title': title,
                'description': description,
                'input_format': input_format,
                'output_format': output_format,
                'sample_cases': sample_cases,
                'hidden_cases': hidden_cases,
                'sample_input': sample_cases[0]['input'] if sample_cases else '',
                'sample_output': sample_cases[0]['output'] if sample_cases else '',
                'hidden_input': hidden_cases[0]['input'] if hidden_cases else '',
                'hidden_output': hidden_cases[0]['output'] if hidden_cases else '',
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
    teacher_dept = (request.user.department or '').strip()
    if teacher_dept:
        if teacher_dept.isdigit():
            classes = Class.objects.filter(
                Q(department__id=int(teacher_dept)) | Q(department__name__iexact=teacher_dept)
            )
        else:
            classes = Class.objects.filter(department__name__iexact=teacher_dept)
    else:
        classes = Class.objects.all()
    
    if request.method == 'POST':
        topic_id = request.POST.get('topic_id')
        bulk_text = request.POST.get('bulk_text', '')
        bulk_purpose = request.POST.get('bulk_purpose', 'both')
        
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
            'bulk_purpose': bulk_purpose,
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
    bulk_purpose = request.POST.get('bulk_purpose', 'both')
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
        target_purpose = request.POST.get(f'purpose_{index}') or bulk_purpose
        if target_purpose not in ['both', 'practice', 'exam']:
            target_purpose = 'both'
        
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
                    
                if target_purpose in ['both', 'practice']:
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
                
                if target_purpose in ['both', 'exam']:
                    exam_mcq = ExamMCQQuestion.objects.create(
                        topic=topic,
                        question_text=q_text,
                        options=options,
                        correct_option_index=correct_idx,
                        explanation=explanation,
                        marks=marks,
                        difficulty=difficulty
                    )
                    if target_purpose == 'exam':
                        created_mcq_ids.append(str(exam_mcq.id))
                
        elif q_type == 'CODING':
            title = request.POST.get(f'title_{index}', '').strip()
            desc = request.POST.get(f'description_{index}', '').strip()
            in_format = request.POST.get(f'input_format_{index}', '').strip()
            out_format = request.POST.get(f'output_format_{index}', '').strip()
            starter = request.POST.get(f'starter_code_{index}', '').strip()
            
            # Read multiple sample test cases
            sample_test_cases = []
            tc_idx = 0
            while True:
                s_inp = request.POST.get(f'sample_input_{index}_{tc_idx}')
                s_out = request.POST.get(f'sample_output_{index}_{tc_idx}')
                if s_inp is None and s_out is None:
                    break
                s_inp = (s_inp or '').strip()
                s_out = (s_out or '').strip()
                if s_inp or s_out:
                    sample_test_cases.append({'input': s_inp, 'output': s_out})
                tc_idx += 1
            if not sample_test_cases:
                s_in = request.POST.get(f'sample_input_{index}', '').strip()
                s_out = request.POST.get(f'sample_output_{index}', '').strip()
                if s_in or s_out:
                    sample_test_cases.append({'input': s_in, 'output': s_out})

            # Read multiple hidden test cases
            hidden_test_cases = []
            tc_idx = 0
            while True:
                h_inp = request.POST.get(f'hidden_input_{index}_{tc_idx}')
                h_out = request.POST.get(f'hidden_output_{index}_{tc_idx}')
                if h_inp is None and h_out is None:
                    break
                h_inp = (h_inp or '').strip()
                h_out = (h_out or '').strip()
                if h_inp or h_out:
                    hidden_test_cases.append({'input': h_inp, 'output': h_out})
                tc_idx += 1
            if not hidden_test_cases:
                h_in = request.POST.get(f'hidden_input_{index}', '').strip()
                h_out = request.POST.get(f'hidden_output_{index}', '').strip()
                if h_in or h_out:
                    hidden_test_cases.append({'input': h_in, 'output': h_out})
                elif sample_test_cases:
                    hidden_test_cases = list(sample_test_cases)
            
            if title and desc and sample_test_cases:
                
                if target_purpose in ['both', 'practice']:
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
                
                if target_purpose in ['both', 'exam']:
                    exam_coding = ExamCodingQuestion.objects.create(
                        topic=topic,
                        title=title,
                        description=desc,
                        input_format=in_format,
                        output_format=out_format,
                        sample_test_cases=sample_test_cases,
                        hidden_test_cases=hidden_test_cases,
                        starter_code=starter,
                        marks=marks,
                        difficulty=difficulty
                    )
                    if target_purpose == 'exam':
                        created_coding_ids.append(str(exam_coding.id))
                
        index += 1
        
    messages.success(
        request, 
        f"Bulk import completed: Saved questions according to topic purpose ({topic.get_purpose_display()})."
    )
    
    mcq_param = ",".join(created_mcq_ids)
    coding_param = ",".join(created_coding_ids)
    return redirect(f'/dashboard/teacher/?imported_mcqs={mcq_param}&imported_codings={coding_param}#questions')
