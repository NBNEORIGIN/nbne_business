from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access control."""

    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('owner', 'Owner'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=30, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    avatar_initials = models.CharField(max_length=4, blank=True, default='')
    is_active_staff = models.BooleanField(default=True, help_text='Whether this staff member is currently active (not Django is_staff)')
    must_change_password = models.BooleanField(default=False, help_text='Force password change on next login')

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'

    @property
    def is_owner(self):
        return self.role == 'owner'

    @property
    def is_manager_or_above(self):
        return self.role in ('manager', 'owner')

    @property
    def is_staff_or_above(self):
        return self.role in ('staff', 'manager', 'owner')

    @property
    def tier(self):
        """Return the highest tier this user can access."""
        if self.role in ('owner', 'manager'):
            return 3
        if self.role == 'staff':
            return 2
        return 1

    def save(self, *args, **kwargs):
        if not self.avatar_initials and self.first_name:
            parts = [self.first_name[0]]
            if self.last_name:
                parts.append(self.last_name[0])
            self.avatar_initials = ''.join(parts).upper()
        super().save(*args, **kwargs)
