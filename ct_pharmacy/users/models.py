from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin (Boss)'),
        ('staff', 'Staff (Doctor/Pharmacist)'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    class Meta:
        db_table = 'users'