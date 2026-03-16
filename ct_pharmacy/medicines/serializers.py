from rest_framework import serializers
from .models import Medicine, Category, Supplier

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'phone', 'email', 'address', 'created_at']

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
            'supplier', 'supplier_name', 'price', 'quantity', 'min_stock_level',
            'expiry_date', 'batch_number', 'description', 'is_low_stock',
            'is_expired', 'is_nearing_expiry', 'created_at', 'updated_at'
        ]