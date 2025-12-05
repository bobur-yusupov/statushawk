from typing import List, Optional
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.password_validation import validate_password

class UserManager(BaseUserManager):
    def create_user(self, email: str, password: Optional[str], **extra_fields) -> 'User':
        if not email:
            raise ValueError("Email is not provided")
        
        email = self.normalize_email(email).lower()
        user: 'User' = self.model(email=email, **extra_fields)

        if password:
            validate_password(password, user)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str) -> 'User':
        user: 'User' = self.create_user(email=email, password=password)
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    id: int = models.AutoField(primary_key=True)
    first_name: str = models.CharField(verbose_name="First Name", max_length=50)
    last_name: str = models.CharField(verbose_name="First Name", max_length=50)
    email: str = models.EmailField(verbose_name="Email", unique=True)
    USERNAME_FIELD: str = 'email'

    is_staff: bool = models.BooleanField(verbose_name="Is Staff", default=False)
    is_superuser: bool = models.BooleanField(verbose_name="Is Superuser", default=False)

    objects = UserManager()

    def __str__(self):
        return f"{self.email}"

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser
