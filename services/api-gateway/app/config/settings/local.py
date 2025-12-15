from typing import List
from .base import *

print("Using local settings...")

ALLOWED_HOSTS: List[str] = ["*"]
DEBUG = True
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-1")
