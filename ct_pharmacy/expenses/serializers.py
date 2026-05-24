from rest_framework import serializers
from .models import ExpenseCategory, Expense


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'description', 'created_at']


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    recorded_by_name = serializers.CharField(
        source='recorded_by.get_full_name',
        read_only=True
    )

    supplier_name = serializers.CharField(
        source='supplier.name',
        read_only=True
    )

    class Meta:
        model = Expense
        fields = [
            'id',
            'expense_id',
            'category',
            'category_name',
            'supplier',
            'supplier_name',
            'description',
            'amount',
            'payment_method',
            'payment_date',
            'recorded_by',
            'recorded_by_name',
            'receipt_number',
            'notes',
            'created_at'
        ]

        # ✅ IMPORTANT FIX
        read_only_fields = [
            'expense_id',
            'created_at',
            'recorded_by'   # 👈 ADD THIS
        ]

    # ✅ AUTO-SET USER
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['recorded_by'] = request.user
        return super().create(validated_data)