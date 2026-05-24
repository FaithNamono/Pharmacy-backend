from rest_framework import serializers
from .models import StockCount, StockCountItem

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