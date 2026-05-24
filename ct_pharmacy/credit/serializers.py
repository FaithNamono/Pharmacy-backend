# ct_pharmacy/credit/serializers.py

from rest_framework import serializers
from datetime import date
from .models import Customer, CreditSale, CreditSaleItem, CreditPayment
from ct_pharmacy.medicines.models import Medicine

class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    total_credit = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    outstanding_balance = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'full_name', 'phone', 'email', 
                  'address', 'id_number', 'total_credit', 'outstanding_balance', 'created_at']

class CreditSaleItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    
    class Meta:
        model = CreditSaleItem
        fields = ['id', 'medicine', 'medicine_name', 'quantity', 'unit_price', 'total_price']

class CreditSaleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    items = CreditSaleItemSerializer(many=True, read_only=True)
    balance = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    is_overdue = serializers.BooleanField(read_only=True)
    issued_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CreditSale
        fields = [
            'id', 'credit_id', 'customer', 'customer_name',
            'items', 'total_amount', 'amount_paid',
            'balance', 'due_date', 'is_overdue',
            'status', 'issued_by', 'issued_by_name', 'notes', 'created_at'
        ]
        read_only_fields = [
            'credit_id', 'amount_paid', 'status', 'created_at', 'issued_by'
        ]

    def get_issued_by_name(self, obj):
        if obj.issued_by:
            user = obj.issued_by
            return user.get_full_name() or user.username
        return ''

class CreditPaymentSerializer(serializers.ModelSerializer):
    credit_id = serializers.CharField(source='credit_sale.credit_id', read_only=True)
    customer_name = serializers.CharField(source='credit_sale.customer.full_name', read_only=True)
    remaining_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = CreditPayment
        fields = ['id', 'credit_sale', 'credit_id', 'customer_name', 'amount', 'payment_date', 
                  'payment_method', 'received_by', 'receipt_number', 'notes', 'remaining_balance']
        read_only_fields = ['payment_date']
    
    def get_remaining_balance(self, obj):
        return float(obj.credit_sale.balance)