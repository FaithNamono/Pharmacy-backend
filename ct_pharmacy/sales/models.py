from django.db import models
from django.conf import settings
from ct_pharmacy.medicines.models import Medicine

class Sale(models.Model):
    sale_id = models.CharField(max_length=50, unique=True)
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='sales')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sales')
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Sale {self.sale_id} - {self.medicine.name}"
    
    def save(self, *args, **kwargs):
        if not self.sale_id:
            last_sale = Sale.objects.order_by('-id').first()
            if last_sale:
                last_number = int(last_sale.sale_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.sale_id = f"SALE-{new_number:06d}"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'sales'
        indexes = [
            models.Index(fields=['sale_date']),
            models.Index(fields=['sale_id']),
        ]