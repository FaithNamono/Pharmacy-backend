# ct_pharmacy/stock/models.py

from django.db import models
from django.conf import settings
from ct_pharmacy.medicines.models import Medicine

class StockCount(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled'),
    )
    
    count_id = models.CharField(max_length=50, unique=True)
    count_date = models.DateTimeField(auto_now_add=True)
    counted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_counts')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_counts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Stock Count {self.count_id} - {self.count_date}"
    
    def save(self, *args, **kwargs):
        if not self.count_id:
            last_count = StockCount.objects.order_by('-id').first()
            if last_count:
                last_number = int(last_count.count_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.count_id = f"SC-{new_number:06d}"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'stock_counts'
        ordering = ['-count_date']

class StockCountItem(models.Model):
    stock_count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    system_quantity = models.IntegerField()
    physical_quantity = models.IntegerField()
    counted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    @property
    def variance(self):
        return self.physical_quantity - self.system_quantity
    
    @property
    def variance_value(self):
        return self.variance * self.medicine.unit_cost
    
    class Meta:
        db_table = 'stock_count_items'
        unique_together = ['stock_count', 'medicine']

# ✅ ADD THIS NEW MODEL
class InventoryHistory(models.Model):
    """Track all inventory changes"""
    
    ACTION_TYPES = (
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('expired', 'Expired'),
        ('write_off', 'Write Off'),
        ('stock_take', 'Stock Take'),
    )
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='inventory_history')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    quantity_changed = models.IntegerField(help_text="Positive for increase, negative for decrease")
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, help_text="Quantity changed × unit cost")
    reference = models.CharField(max_length=100, blank=True, help_text="Reference like sale ID, purchase order, etc.")
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['medicine']),
            models.Index(fields=['action_type']),
        ]
    
    def __str__(self):
        return f"{self.medicine.name} - {self.action_type} - {self.quantity_changed} units"
    
    @property
    def total_value_display(self):
        return f"UGX {self.total_value:,.0f}"