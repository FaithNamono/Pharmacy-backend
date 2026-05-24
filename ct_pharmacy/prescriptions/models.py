from django.db import models
from django.conf import settings
from ct_pharmacy.medicines.models import Medicine

class Prescription(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('filled', 'Filled'),
        ('partially_filled', 'Partially Filled'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    prescription_id = models.CharField(max_length=50, unique=True)
    patient_name = models.CharField(max_length=200)
    patient_age = models.IntegerField(null=True, blank=True)
    patient_phone = models.CharField(max_length=15, blank=True)
    doctor_name = models.CharField(max_length=200)
    doctor_license = models.CharField(max_length=100, blank=True)
    hospital = models.CharField(max_length=200, blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    diagnosis = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    prescription_image = models.ImageField(upload_to='prescriptions/', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"RX {self.prescription_id} - {self.patient_name}"
    
    @property
    def is_expired(self):
        from datetime import date
        return date.today() > self.expiry_date
    
    def save(self, *args, **kwargs):
        if not self.prescription_id:
            last_rx = Prescription.objects.order_by('-id').first()
            if last_rx:
                last_number = int(last_rx.prescription_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.prescription_id = f"RX-{new_number:06d}"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    prescribed_quantity = models.IntegerField()
    filled_quantity = models.IntegerField(default=0)
    dosage_instructions = models.TextField()
    duration = models.CharField(max_length=100, blank=True)
    
    @property
    def remaining_quantity(self):
        return self.prescribed_quantity - self.filled_quantity
    
    @property
    def is_fully_filled(self):
        return self.filled_quantity >= self.prescribed_quantity
    
    class Meta:
        db_table = 'prescription_items'