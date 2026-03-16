from django.db import models
from datetime import date

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        db_table = 'categories'

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'suppliers'

class Medicine(models.Model):
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='medicines')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='medicines')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=10, help_text="Minimum quantity before low stock alert")
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.batch_number}"
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level
    
    @property
    def is_expired(self):
        return self.expiry_date < date.today()
    
    @property
    def is_nearing_expiry(self):
        days_until_expiry = (self.expiry_date - date.today()).days
        return 0 <= days_until_expiry <= 30
    
    class Meta:
        db_table = 'medicines'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['expiry_date']),
        ]