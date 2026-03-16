from rest_framework import serializers
from datetime import date
from .models import Sale
from ct_pharmacy.medicines.models import Medicine

class SaleSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    staff_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'sale_id', 'medicine', 'medicine_name', 'user', 'staff_name',
            'quantity', 'unit_price', 'total_price', 'sale_date', 'notes'
        ]
        read_only_fields = ['sale_id', 'total_price', 'sale_date', 'unit_price']

    def validate(self, data):
        medicine = data.get('medicine')
        quantity = data.get('quantity')
        
        if medicine and quantity:
            # CRITICAL: Check if medicine is expired
            today = date.today()
            if medicine.expiry_date < today:
                raise serializers.ValidationError({
                    'medicine': f"Cannot sell expired medicine: {medicine.name}. "
                               f"Expired on {medicine.expiry_date.strftime('%Y-%m-%d')}"
                })
            
            # Check stock availability
            if medicine.quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': f"Insufficient stock. Available: {medicine.quantity}"
                })
        return data

    def create(self, validated_data):
        medicine = validated_data['medicine']
        quantity = validated_data['quantity']
        
        # Calculate total price
        validated_data['unit_price'] = medicine.price
        validated_data['total_price'] = medicine.price * quantity
        
        # Update stock
        medicine.quantity -= quantity
        medicine.save()
        
        return super().create(validated_data)