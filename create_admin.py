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

from accounts.models import User

def create_admin():
    print("=========================================================")
    print("              ADMIN USER CREATION SCRIPT                 ")
    print("=========================================================\n")

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@eduexam.edu")
    admin_password = os.getenv("ADMIN_PASSWORD", "AdminPassword123")

    user, created = User.objects.get_or_create(username=admin_username)
    
    user.email = admin_email
    user.set_password(admin_password)
    user.first_name = "System"
    user.last_name = "Admin"
    user.role = "admin"
    user.is_superuser = True
    user.is_staff = True
    user.is_approved = True
    user.save()

    status_str = "Created new" if created else "Updated existing"
    print(f"SUCCESS: {status_str} Admin account (@{admin_username}).\n")

    credentials = (
        "=========================================================\n"
        "                ADMIN USER CREDENTIALS                   \n"
        "=========================================================\n"
        f"Username: {admin_username}\n"
        f"Email:    {admin_email}\n"
        f"Role:     Admin / Superuser\n"
        f"Password: {admin_password}\n"
        "=========================================================\n"
    )

    # Save admin credentials to text file
    output_filename = "admin_credentials.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(credentials)

    print(credentials)
    print(f"Credentials saved to '{output_filename}'.")

if __name__ == "__main__":
    create_admin()
