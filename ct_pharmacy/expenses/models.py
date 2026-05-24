from django.db import models
from django.conf import settings
from ct_pharmacy.medicines.models import Supplier

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Expense Categories" 
        db_table = 'expense_categories'
        ordering = ['name']

class Expense(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('credit', 'Credit'),
        ('cheque', 'Cheque'),
    )
    
    expense_id = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_date = models.DateField()
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='expenses'  # Make sure this exists
    )
    receipt_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Expense {self.expense_id} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.expense_id:
            last_expense = Expense.objects.order_by('-id').first()
            if last_expense:
                last_number = int(last_expense.expense_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.expense_id = f"EXP-{new_number:06d}"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'expenses'
        ordering = ['-payment_date']