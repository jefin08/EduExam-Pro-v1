from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager

class CustomUserManager(DjangoUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        role = extra_fields.get('role', 'student')
        if role == 'teacher':
            extra_fields.setdefault('is_staff', True)
        elif role == 'admin':
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_approved', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)

class Class(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    department = models.CharField(max_length=100, blank=True, null=True, help_text="Teacher department classification")
    is_approved = models.BooleanField(default=True, help_text="Approval gate for self-registered teacher accounts")
    class_group = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
