from typing import List
import os
from .base import *  # noqa

print("Production Settings")

ALLOWED_HOSTS: List[str] = ["*"]
DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-1")
