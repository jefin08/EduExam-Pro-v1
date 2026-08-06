import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from django.db import connection, transaction
from django.apps import apps

def clear_database():
    print("Clearing database data while preserving admins and schemas...")
    
    # Disable foreign key constraints to allow safe deletion of related records
    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
    try:
        # Fetch all models registered in Django
        all_models = apps.get_models()
        
        for model in all_models:
            model_name = model.__name__
            app_label = model._meta.app_label
            
            # Skip core Django authentication/permissions/contenttype metadata
            if app_label in ['contenttypes', 'auth'] and model_name in ['Permission', 'ContentType', 'Group']:
                continue
                
            # Skip django migration history
            if app_label == 'migrations':
                continue
                
            if model_name == 'User':
                # Delete only non-admin users (preserve superusers and role='admin')
                non_admins = model.objects.exclude(is_superuser=True).exclude(role='admin')
                count = non_admins.count()
                if count > 0:
                    non_admins.delete()
                    print(f" - Deleted {count} non-admin user(s) from accounts.User")
            else:
                # Delete all records from this table
                count = model.objects.count()
                if count > 0:
                    model.objects.all().delete()
                    print(f" - Deleted {count} record(s) from {app_label}.{model_name}")
                    
        print("\nDatabase data cleared successfully!")
        
    except Exception as e:
        print(f"Error occurred during database clearing: {e}")
        raise e
    finally:
        # Re-enable foreign key constraints
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

if __name__ == '__main__':
    confirm = input("WARNING: This will delete all students, teachers, classes, exams, questions, and attempts.\n"
                    "Only admin accounts will be preserved.\n"
                    "Are you sure you want to proceed? (yes/no): ")
    if confirm.lower() == 'yes':
        try:
            with transaction.atomic():
                clear_database()
        except Exception as e:
            print("Transaction rolled back due to error.")
            sys.exit(1)
    else:
        print("Operation cancelled.")
