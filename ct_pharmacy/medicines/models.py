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
    name = models.CharField(max_length=200)  # Only required field
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'suppliers'

class Medicine(models.Model):
    UNIT_CHOICES = (
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('bottle', 'Bottle'),
        ('strip', 'Strip'),
        ('box', 'Box'),
        ('pack', 'Pack'),
        ('ml', 'Milliliter'),
        ('g', 'Gram'),
    )
    
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='medicines')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
    
    # Pricing fields
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Cost price per unit")
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Wholesale selling price")
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Retail selling price")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Default discount %")
    
    # Stock fields
    quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=10, help_text="Minimum quantity before low stock alert")
    unit_type = models.CharField(max_length=20, choices=UNIT_CHOICES, default='tablet')
    units_per_pack = models.IntegerField(default=1, help_text="Number of units per pack/strip/bottle")
    
    # Expiry and tracking
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=100, blank=True, help_text="QR/Bar code for scanning")
    description = models.TextField(blank=True)
    
    # Timestamps
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
    
    @property
    def total_cost(self):
        """Total cost value of current stock"""
        return self.quantity * self.unit_cost
    
    @property
    def total_retail_value(self):
        """Total retail value of current stock"""
        return self.quantity * self.retail_price
    
    @property
    def total_wholesale_value(self):
        """Total wholesale value of current stock"""
        return self.quantity * self.wholesale_price
    
    @property
    def profit_margin(self):
        """Profit margin percentage"""
        if self.unit_cost > 0:
            return ((self.retail_price - self.unit_cost) / self.unit_cost) * 100
        return 0
    
    class Meta:
        db_table = 'medicines'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['expiry_date']),
        ]