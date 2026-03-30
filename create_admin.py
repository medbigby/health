import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'mohamed.bouzidi03@gmail.com', 'admin123')
    print("Superuser created: username=admin, password=admin123")
else:
    print("Superuser already exists")