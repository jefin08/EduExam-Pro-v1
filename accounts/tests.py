from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Class

User = get_user_model()

class AccountsModelTests(TestCase):
    def setUp(self):
        self.class_group = Class.objects.create(name="Computer Science 101")

    def test_class_creation(self):
        self.assertEqual(str(self.class_group), "Computer Science 101")

    def test_user_roles(self):
        admin_user = User.objects.create_superuser(
            username="admin_user",
            email="admin@test.com",
            password="testpassword",
            role="admin"
        )
        teacher_user = User.objects.create_user(
            username="teacher_user",
            email="teacher@test.com",
            password="testpassword",
            role="teacher"
        )
        student_user = User.objects.create_user(
            username="student_user",
            email="student@test.com",
            password="testpassword",
            role="student",
            class_group=self.class_group
        )

        self.assertEqual(admin_user.role, "admin")
        self.assertEqual(teacher_user.role, "teacher")
        self.assertEqual(student_user.role, "student")
        self.assertEqual(student_user.class_group, self.class_group)
