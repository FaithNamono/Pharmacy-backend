# ct_pharmacy/stock/serializers.py

from rest_framework import serializers
from .models import StockCount, StockCountItem, InventoryHistory
from ct_pharmacy.medicines.models import Medicine

class StockCountItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    variance = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = StockCountItem
        fields = ['id', 'medicine', 'medicine_name', 'system_quantity', 'physical_quantity',
                  'variance', 'counted_at', 'notes']

class StockCountSerializer(serializers.ModelSerializer):
    items = StockCountItemSerializer(many=True, read_only=True)
    counted_by_name = serializers.CharField(source='counted_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    
    class Meta:
        model = StockCount
        fields = ['id', 'count_id', 'count_date', 'counted_by', 'counted_by_name',
                  'verified_by', 'verified_by_name', 'status', 'notes', 'items']
        read_only_fields = ['count_id', 'count_date']

    def create(self, validated_data):
        validated_data['counted_by'] = self.context['request'].user
        return super().create(validated_data)

# ✅ ADD THIS SERIALIZER
class InventoryHistorySerializer(serializers.ModelSerializer):
    """Serializer for Inventory History"""
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_category = serializers.CharField(source='medicine.category.name', read_only=True, default='')
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    class Meta:
        model = InventoryHistory
        fields = [
            'id', 'medicine', 'medicine_name', 'medicine_category',
            'action_type', 'action_display', 'quantity_changed',
            'previous_quantity', 'new_quantity', 'unit_cost',
            'total_value', 'reference', 'notes', 'performed_by',
            'performed_by_name', 'created_at'
        ]
        read_only_fields = ['created_at']

class InventorySummarySerializer(serializers.Serializer):
    """Serializer for inventory summary"""
    total_medicines = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_restock_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_sale_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    recent_activity_count = serializers.IntegerField()