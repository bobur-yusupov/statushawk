from typing import Optional, Any, cast
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.password_validation import validate_password


class UserManager(BaseUserManager):
    def create_user(
        self, email: str, password: Optional[str], **extra_fields: Any
    ) -> "User":
        if not email:
            raise ValueError("Email is not provided")

        email = self.normalize_email(email).lower()
        user = cast("User", self.model(email=email, **extra_fields))

        if password:
            validate_password(password, user)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str) -> "User":
        user = self.create_user(email=email, password=password)
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(verbose_name="First Name", max_length=50)
    last_name = models.CharField(verbose_name="First Name", max_length=50)
    email = models.EmailField(verbose_name="Email", unique=True)
    USERNAME_FIELD = "email"

    is_staff = models.BooleanField(verbose_name="Is Staff", default=False)
    is_superuser = models.BooleanField(verbose_name="Is Superuser", default=False)

    objects = UserManager()

    def __str__(self) -> str:
        return f"{self.email}"

    def has_perm(self, perm: str, obj: Any = None) -> bool:
        return self.is_superuser

    def has_module_perms(self, app_label: str) -> bool:
        return self.is_superuser
