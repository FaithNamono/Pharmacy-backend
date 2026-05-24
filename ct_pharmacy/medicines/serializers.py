from rest_framework import serializers
from datetime import date
from .models import Medicine, Category, Supplier

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'phone', 'email', 'address', 'created_at']
        extra_kwargs = {
            'contact_person': {'required': False, 'allow_blank': True, 'allow_null': True},
            'phone': {'required': False, 'allow_blank': True, 'allow_null': True},
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'address': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_nearing_expiry = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'category', 'category_name',
            'supplier', 'supplier_name', 
            'unit_cost', 'wholesale_price', 'retail_price', 'discount_percentage',
            'quantity', 'min_stock_level', 'unit_type', 'units_per_pack', 'barcode',
            'expiry_date', 'batch_number', 'description', 'is_low_stock',
            'is_expired', 'is_nearing_expiry', 'created_at', 'updated_at'
        ]

    def validate_expiry_date(self, value):
        """Validate that expiry date is in the future"""
        today = date.today()
        if value < today:
            raise serializers.ValidationError(
                f"Expiry date cannot be in the past. Today is {today.strftime('%Y-%m-%d')}, "
                f"you selected {value.strftime('%Y-%m-%d')}"
            )
        return value