# ct_pharmacy/prescriptions/admin.py

from django.contrib import admin
from .models import Prescription, PrescriptionItem

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1
    fields = ['medicine', 'quantity', 'dosage_instructions', 'duration']
    raw_id_fields = ['medicine']

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_id', 'patient_name', 'doctor_name', 'status', 'issue_date', 'expiry_date')
    list_filter = ('status', 'issue_date', 'expiry_date')
    search_fields = ('prescription_id', 'patient_name', 'doctor_name')
    inlines = [PrescriptionItemInline]
    readonly_fields = ('prescription_id', 'created_at')