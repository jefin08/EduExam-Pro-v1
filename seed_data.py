import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django environment: {e}")
    sys.exit(1)

from django.db import transaction
from accounts.models import User, Class, Department

def seed_database():
    print("Starting database seeding: 1 Admin, 2 Teachers (2 Departments), 20 Students...")
    
    # 1. Create or get Departments
    department_names = [
        "Computer Science",
        "Information Technology"
    ]
    
    departments = {}
    print("\nCreating/Verifying Departments:")
    for name in department_names:
        dept_obj, created = Department.objects.get_or_create(name=name)
        departments[name] = dept_obj
        status = "Created" if created else "Already Exists"
        print(f" - {name} ({status})")

    # 2. Create or get Classes
    class_names = [
        "Computer Science",
        "Information Technology"
    ]
    
    classes = {}
    print("\nCreating/Verifying Classes:")
    for name in class_names:
        class_obj, created = Class.objects.get_or_create(name=name)
        classes[name] = class_obj
        status = "Created" if created else "Already Exists"
        print(f" - {name} ({status})")

    credentials_log = []
    credentials_log.append("=================================================================")
    credentials_log.append("                   SYSTEM USER CREDENTIALS                       ")
    credentials_log.append("=================================================================\n")

    # 3. Create Admin
    admin_username = "admin"
    admin_email = "admin@eduexam.edu"
    admin_password = "AdminPassword123"
    
    print("\nCreating/Verifying Admin User:")
    admin_user = User.objects.filter(username=admin_username).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name="System",
            last_name="Admin",
            role="admin",
            is_approved=True
        )
        print(f" - Created Admin: @{admin_username}")
    else:
        admin_user.set_password(admin_password)
        admin_user.role = "admin"
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.is_approved = True
        admin_user.save()
        print(f" - Updated existing Admin: @{admin_username}")

    credentials_log.append("1. ADMIN ACCOUNT")
    credentials_log.append("-" * 40)
    credentials_log.append(f"Username: {admin_username}")
    credentials_log.append(f"Email:    {admin_email}")
    credentials_log.append(f"Role:     Admin / Superuser")
    credentials_log.append(f"Password: {admin_password}\n")

    # 4. Create 2 Teachers for 2 different departments
    teachers_data = [
        {
            "username": "teacher_cs",
            "email": "teacher.cs@eduexam.edu",
            "first_name": "Alan",
            "last_name": "Turing",
            "department": "Computer Science",
            "password": "TeacherPassword123"
        },
        {
            "username": "teacher_it",
            "email": "teacher.it@eduexam.edu",
            "first_name": "Grace",
            "last_name": "Hopper",
            "department": "Information Technology",
            "password": "TeacherPassword123"
        }
    ]

    print("\nCreating/Verifying 2 Teachers (2 Departments):")
    credentials_log.append("2. TEACHER ACCOUNTS (2 DEPARTMENTS)")
    credentials_log.append("-" * 40)
    
    for t in teachers_data:
        user = User.objects.filter(username=t["username"]).first()
        if not user:
            user = User.objects.create_user(
                username=t["username"],
                email=t["email"],
                password=t["password"],
                first_name=t["first_name"],
                last_name=t["last_name"],
                role="teacher",
                department=t["department"],
                is_approved=True
            )
            print(f" - Created Teacher: {user.first_name} {user.last_name} (@{user.username}) - Dept: {user.department}")
        else:
            user.set_password(t["password"])
            user.department = t["department"]
            user.role = "teacher"
            user.is_approved = True
            user.save()
            print(f" - Updated Teacher: @{t['username']}")
            
        credentials_log.append(f"Username:   {t['username']}")
        credentials_log.append(f"Email:      {t['email']}")
        credentials_log.append(f"Department: {t['department']}")
        credentials_log.append(f"Password:   {t['password']}")
        credentials_log.append("")

    # 5. Create 20 Students
    student_first_names = [
        "John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah",
        "Ian", "Julia", "Kevin", "Laura", "Michael", "Nina", "Oscar", "Paula", "Quinn", "Rachel"
    ]
    student_last_names = [
        "Doe", "Smith", "Johnson", "Brown", "Davis", "Evans", "Wilson", "Clark", "Harris", "Lewis",
        "Walker", "Hall", "Allen", "Young", "King", "Wright", "Scott", "Green", "Adams", "Baker"
    ]

    print("\nCreating/Verifying 20 Students:")
    credentials_log.append("3. STUDENT ACCOUNTS (20 STUDENTS)")
    credentials_log.append("-" * 40)

    for i in range(1, 21):
        username = f"student_{i:02d}"
        email = f"student.{i:02d}@eduexam.edu"
        password = "StudentPassword123"
        first_name = student_first_names[i - 1]
        last_name = student_last_names[i - 1]
        
        # Alternate between the 2 classes
        class_name = "Computer Science" if i % 2 != 0 else "Information Technology"
        class_group = classes.get(class_name)

        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role="student",
                class_group=class_group,
                is_approved=True
            )
            print(f" - Created Student ({i}/20): {first_name} {last_name} (@{username}) - Class: {class_name}")
        else:
            user.set_password(password)
            user.class_group = class_group
            user.role = "student"
            user.is_approved = True
            user.save()
            print(f" - Updated Student ({i}/20): @{username}")

        credentials_log.append(f"Student {i:02d} | Username: {username} | Email: {email} | Class: {class_name} | Password: {password}")

    # Write credentials to text file
    output_filename = "user_credentials.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(credentials_log))

    print(f"\nSeeding completed successfully! Credentials written to '{output_filename}'.")

if __name__ == "__main__":
    try:
        with transaction.atomic():
            seed_database()
    except Exception as e:
        print(f"\nAn error occurred during database seeding: {e}")
        sys.exit(1)
