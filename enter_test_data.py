import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django environment: {e}")
    print("Please make sure you run this script from the project root directory where 'manage.py' is located, and that your virtual environment is activated.")
    sys.exit(1)

from django.db import transaction
from accounts.models import User, Class, Department

def seed_database():
    print("Starting database seeding for 10 Students and 5 Teachers...")
    
    # 1. Create or get Classes
    class_names = [
        "Computer Science",
        "Information Technology",
        "Mathematics",
        "Electronics"
    ]
    
    classes = {}
    print("\nCreating/Verifying Classes:")
    for name in class_names:
        class_obj, created = Class.objects.get_or_create(name=name)
        classes[name] = class_obj
        status = "Created" if created else "Already Exists"
        print(f" - {name} ({status})")

    # 1b. Create or get Departments
    department_names = [
        "Computer Science",
        "Information Technology",
        "Mathematics",
        "Physics",
        "Chemistry",
        "Electronics"
    ]
    
    print("\nCreating/Verifying Departments:")
    for name in department_names:
        dept_obj, created = Department.objects.get_or_create(name=name)
        status = "Created" if created else "Already Exists"
        print(f" - {name} ({status})")

    # 2. Teacher Data to insert (5 teachers)
    teachers_data = [
        {
            "username": "alan_turing",
            "email": "alan.turing@eduexam.edu",
            "first_name": "Alan",
            "last_name": "Turing",
            "department": "Computer Science",
            "password": "Password123"
        },
        {
            "username": "grace_hopper",
            "email": "grace.hopper@eduexam.edu",
            "first_name": "Grace",
            "last_name": "Hopper",
            "department": "Information Technology",
            "password": "Password123"
        },
        {
            "username": "ada_lovelace",
            "email": "ada.lovelace@eduexam.edu",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "department": "Mathematics",
            "password": "Password123"
        },
        {
            "username": "richard_feynman",
            "email": "richard.feynman@eduexam.edu",
            "first_name": "Richard",
            "last_name": "Feynman",
            "department": "Physics",
            "password": "Password123"
        },
        {
            "username": "marie_curie",
            "email": "marie.curie@eduexam.edu",
            "first_name": "Marie",
            "last_name": "Curie",
            "department": "Chemistry",
            "password": "Password123"
        }
    ]

    print("\nCreating/Verifying Teachers:")
    for t in teachers_data:
        # Check if user already exists
        user_exists = User.objects.filter(username=t["username"]).exists()
        if not user_exists:
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
            print(f" - Teacher @{t['username']} already exists.")

    # 3. Student Data to insert (10 students)
    students_data = [
        {
            "username": "john_doe",
            "email": "john.doe@student.edu",
            "first_name": "John",
            "last_name": "Doe",
            "class_name": "Computer Science",
            "password": "Password123"
        },
        {
            "username": "jane_smith",
            "email": "jane.smith@student.edu",
            "first_name": "Jane",
            "last_name": "Smith",
            "class_name": "Computer Science",
            "password": "Password123"
        },
        {
            "username": "bob_johnson",
            "email": "bob.johnson@student.edu",
            "first_name": "Bob",
            "last_name": "Johnson",
            "class_name": "Information Technology",
            "password": "Password123"
        },
        {
            "username": "alice_brown",
            "email": "alice.brown@student.edu",
            "first_name": "Alice",
            "last_name": "Brown",
            "class_name": "Information Technology",
            "password": "Password123"
        },
        {
            "username": "charlie_davis",
            "email": "charlie.davis@student.edu",
            "first_name": "Charlie",
            "last_name": "Davis",
            "class_name": "Mathematics",
            "password": "Password123"
        },
        {
            "username": "diana_evans",
            "email": "diana.evans@student.edu",
            "first_name": "Diana",
            "last_name": "Evans",
            "class_name": "Mathematics",
            "password": "Password123"
        },
        {
            "username": "ethan_wilson",
            "email": "ethan.wilson@student.edu",
            "first_name": "Ethan",
            "last_name": "Wilson",
            "class_name": "Computer Science",
            "password": "Password123"
        },
        {
            "username": "fiona_clark",
            "email": "fiona.clark@student.edu",
            "first_name": "Fiona",
            "last_name": "Clark",
            "class_name": "Information Technology",
            "password": "Password123"
        },
        {
            "username": "george_harris",
            "email": "george_harris@student.edu",
            "first_name": "George",
            "last_name": "Harris",
            "class_name": "Electronics",
            "password": "Password123"
        },
        {
            "username": "hannah_lewis",
            "email": "hannah.lewis@student.edu",
            "first_name": "Hannah",
            "last_name": "Lewis",
            "class_name": "Electronics",
            "password": "Password123"
        }
    ]

    print("\nCreating/Verifying Students:")
    for s in students_data:
        # Check if user already exists
        user_exists = User.objects.filter(username=s["username"]).exists()
        if not user_exists:
            class_group = classes.get(s["class_name"])
            user = User.objects.create_user(
                username=s["username"],
                email=s["email"],
                password=s["password"],
                first_name=s["first_name"],
                last_name=s["last_name"],
                role="student",
                class_group=class_group,
                is_approved=True
            )
            print(f" - Created Student: {user.first_name} {user.last_name} (@{user.username}) - Class: {user.class_group.name if user.class_group else 'None'}")
        else:
            print(f" - Student @{s['username']} already exists.")

    print("\nDatabase seeding completed successfully!")

if __name__ == "__main__":
    try:
        with transaction.atomic():
            seed_database()
    except Exception as e:
        print(f"\nAn error occurred during database seeding: {e}")
        sys.exit(1)
