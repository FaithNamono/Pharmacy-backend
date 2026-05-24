from django.db import models
from django.conf import settings
from ct_pharmacy.medicines.models import Medicine

class Sale(models.Model):
    SALE_TYPE_CHOICES = (
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
    )
    
    sale_id = models.CharField(max_length=50, blank=True)  # Remove unique=True
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='sales')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sales')
    prescription = models.ForeignKey('prescriptions.Prescription', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_type = models.CharField(max_length=20, choices=SALE_TYPE_CHOICES, default='retail')
    sale_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    payment_method = models.CharField(max_length=50, default='Cash')
    
    def __str__(self):
        return f"Sale {self.sale_id} - {self.medicine.name}"
    
    def save(self, *args, **kwargs):
        # Get prices from medicine if not set
        if self.medicine:
            if self.sale_type == 'wholesale':
                self.unit_price = self.medicine.wholesale_price
            else:
                self.unit_price = self.medicine.retail_price
            self.unit_cost = self.medicine.unit_cost if hasattr(self.medicine, 'unit_cost') else 0
            
        # Calculate prices
        self.subtotal = self.unit_price * self.quantity
        self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        self.total_price = self.subtotal - self.discount_amount
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'sales'
        indexes = [
            models.Index(fields=['sale_date']),
            models.Index(fields=['sale_id']),
        ]

    @property
    def medicine_name(self):
        return self.medicine.name if self.medicine else ''
    
    @property
    def staff_name(self):
        return self.user.get_full_name() or self.user.username