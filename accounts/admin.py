from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Class, Department

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'class_group', 'is_staff']
    list_filter = ['role', 'class_group', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile Information', {'fields': ('role', 'class_group', 'department', 'is_approved')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile Information', {'fields': ('role', 'class_group', 'department', 'is_approved')}),
    )

class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'created_at']
    list_filter = ['department']
    search_fields = ['name', 'department__name']

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

admin.site.register(User, CustomUserAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Department, DepartmentAdmin)

