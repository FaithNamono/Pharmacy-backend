from rest_framework import serializers
from .models import Prescription, PrescriptionItem
from ct_pharmacy.medicines.models import Medicine

class PrescriptionItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_id = serializers.IntegerField(source='medicine.id', read_only=True)
    
    class Meta:
        model = PrescriptionItem
        fields = ['id', 'medicine', 'medicine_id', 'medicine_name', 'prescribed_quantity', 
                  'filled_quantity', 'remaining_quantity', 'dosage_instructions', 'duration']
        read_only_fields = ['filled_quantity', 'remaining_quantity']

class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    prescription_image = serializers.ImageField(required=False, allow_null=True)  # Add this

    class Meta:
        model = Prescription
        fields = ['id', 'prescription_id', 'patient_name', 'patient_age', 'patient_phone',
                  'doctor_name', 'doctor_license', 'hospital', 'issue_date', 'expiry_date',
                  'diagnosis', 'status', 'is_expired', 'notes', 'prescription_image',
                  'created_by', 'created_by_name', 'created_at', 'items']
        read_only_fields = ['prescription_id', 'created_at', 'created_by']

class FillPrescriptionSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    quantity_filled = serializers.IntegerField()