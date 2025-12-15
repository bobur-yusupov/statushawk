from typing import List
from .base import *

print("Production Settings")

ALLOWED_HOSTS: List[str] = ["*"]
DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-1")
