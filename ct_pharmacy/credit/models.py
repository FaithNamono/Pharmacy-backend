# ct_pharmacy/credit/models.py

from django.db import models
from django.conf import settings
from decimal import Decimal
from ct_pharmacy.medicines.models import Medicine

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True)
    address = models.TextField()
    id_number = models.CharField(max_length=50, blank=True, help_text="National ID/Passport")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='credit_sales_issued'  
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_credit(self):
        total = self.creditsales.aggregate(total=models.Sum('total_amount'))['total']
        return total or Decimal('0.00')
    
    @property
    def outstanding_balance(self):
        total = self.creditsales.aggregate(
            total=models.Sum(models.F('total_amount') - models.F('amount_paid'))
        )['total']
        return total or Decimal('0.00')
    
    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']


class CreditSale(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('defaulted', 'Defaulted'),
    )
    
    credit_id = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='creditsales')
    # REMOVED: medicine, quantity, unit_price fields - they now go to CreditSaleItem
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    prescription = models.ForeignKey('prescriptions.Prescription', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Credit {self.credit_id} - {self.customer.full_name}"
    
    @property
    def balance(self):
        return self.total_amount - self.amount_paid
    
    @property
    def is_overdue(self):
        from datetime import date
        return date.today() > self.due_date and self.balance > Decimal('0.00')
    
    def save(self, *args, **kwargs):
        if not self.credit_id:
            last_credit = CreditSale.objects.order_by('-id').first()
            if last_credit:
                last_number = int(last_credit.credit_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.credit_id = f"CR-{new_number:06d}"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'credit_sales'
        ordering = ['-created_at']


class CreditSaleItem(models.Model):
    """Individual items in a credit sale"""
    credit_sale = models.ForeignKey(CreditSale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
    
    class Meta:
        db_table = 'credit_sale_items'


class CreditPayment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
    )
    
    credit_sale = models.ForeignKey(CreditSale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    receipt_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'credit_payments'
        ordering = ['-payment_date']