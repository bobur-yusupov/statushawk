import random
from typing import Any
from faker import Faker
from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model
from django.db import transaction
from monitor.models import Monitor

fake = Faker()

# Real sites for "UP" status (Safe to ping occasionally)
SAFE_URLS = [
    "https://www.google.com",
    "https://www.github.com",
    "https://www.stackoverflow.com",
    "https://www.python.org",
    "https://www.djangoproject.com",
    "https://www.cloudflare.com",
    "https://www.bing.com",
    "https://www.wikipedia.org",
    "https://www.amazon.com",
]

# Broken sites for "DOWN" status
# (These domains usually don't exist or block connections)
BROKEN_URLS = [
    "https://this-site-does-not-exist-12345.com",
    "http://localhost:9999",  # Connection refused
    "https://expired.badssl.com",  # SSL Error
    "http://httpstat.us/500",  # Returns 500 Error
    "http://httpstat.us/404",  # Returns 404 Error
    "http://httpstat.us/200?sleep=5000",  # Slow response
]


class Command(BaseCommand):
    help = "Populate DB with realistic fake data for testing"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--users", type=int, default=5, help="How many users to create"
        )
        parser.add_argument(
            "--monitors", type=int, default=20, help="Monitors per user"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        User = get_user_model()
        num_users = options["users"]
        monitors_per_user = options["monitors"]

        self.stdout.write(
            f"🌱 Seeding {num_users} users with {monitors_per_user} monitors each..."
        )

        with transaction.atomic():
            # 1. Create Users
            users = []
            for _ in range(num_users):
                email = fake.unique.email()
                user, created = User.objects.get_or_create(email=email, defaults={})
                if created:
                    user.set_password("password123")
                    user.save()
                users.append(user)

            # 2. Create Monitors for each User
            total_monitors = 0
            for user in users:
                for _ in range(monitors_per_user):
                    # Randomly decide if this monitor should pass or fail
                    is_broken = random.choice(
                        [True, False, False, False]
                    )  # 25% chance of broken

                    if is_broken:
                        target_url = random.choice(BROKEN_URLS)
                        name_prefix = "⚠️ [TEST DOWN]"
                    else:
                        target_url = random.choice(SAFE_URLS)
                        # Add random query param to make URL unique in DB/logs
                        target_url += f"?q={fake.uuid4()}"
                        name_prefix = "✅ [TEST UP]"

                    # Generate a cool sounding service name
                    # e.g. "Redis Cluster - Production", "Payment Gateway API"
                    service_name = (
                        f"{fake.word().capitalize()} "
                        f"{random.choice([
                            'Service',
                            'Cluster',
                            'API',
                            'Worker',
                            'DB'
                        ])}"
                    )
                    full_name = f"{name_prefix} {service_name}"

                    Monitor.objects.create(
                        user=user,
                        name=full_name,
                        url=target_url,
                        monitor_type=Monitor.MonitorType.HTTP,
                        interval=random.choice([30, 60, 300]),  # Random interval
                        is_active=True,
                    )
                    total_monitors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Done! Created {len(users)} users and "
                f"{total_monitors} monitors.\n"
                f"👉 Login with: {users[0].email} / password123"
            )
        )
