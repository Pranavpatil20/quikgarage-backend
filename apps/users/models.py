from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils import timezone


class UserRole(models.TextChoices):
    OWNER = 'owner', 'Owner'
    CUSTOMER = 'customer', 'Customer'


class UserManager(BaseUserManager):
    def create_user(self, phone, name='', role=UserRole.CUSTOMER, password=None, **extra):
        if not phone:
            raise ValueError('Phone number is required')
        user = self.model(phone=phone, name=name, role=role, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, name='Admin', password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', UserRole.OWNER)
        return self.create_user(phone, name, UserRole.OWNER, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    name = models.CharField(max_length=120, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CUSTOMER)
    firebase_uid = models.CharField(max_length=128, blank=True, null=True, unique=True)
    fcm_token = models.TextField(blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    subscription_paid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name or self.phone} ({self.role})'

    @property
    def is_owner(self):
        return self.role == UserRole.OWNER

    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER

    @property
    def subscription_active(self) -> bool:
        if not self.is_owner:
            return True
        now = timezone.now()
        if self.trial_ends_at and now < self.trial_ends_at:
            return True
        if self.subscription_paid_until and now.date() <= self.subscription_paid_until:
            return True
        return False

    @property
    def is_payment_locked(self) -> bool:
        return self.is_owner and not self.subscription_active
