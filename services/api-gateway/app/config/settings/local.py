from typing import List
import os
from .base import *  # noqa

print("Using local settings...")

ALLOWED_HOSTS: List[str] = ["*"]
DEBUG = True
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-1")

import sentry_sdk

sentry_sdk.init(
    dsn="https://148164fef2a93ce6eda4427222973ee8@o4510539645321216.ingest.de.sentry.io/4510539646632016",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)
