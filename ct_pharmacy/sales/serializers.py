# ct_pharmacy/sales/serializers.py

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
            'quantity', 'unit_price', 'total_price', 'sale_date', 'notes',
            'customer_name', 'payment_method', 'sale_type'
        ]
        read_only_fields = ['sale_id', 'total_price', 'sale_date', 'unit_price']

    def validate(self, data):
        medicine = data.get('medicine')
        quantity = data.get('quantity')
        
        if medicine and quantity:
            # Check if medicine is expired
            if medicine.expiry_date and medicine.expiry_date < date.today():
                raise serializers.ValidationError({
                    'medicine': f"Cannot sell expired medicine: {medicine.name}"
                })
            # Check stock
            if medicine.quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': f"Insufficient stock. Available: {medicine.quantity}"
                })
        return data

    def create(self, validated_data):
        medicine = validated_data['medicine']
        quantity = validated_data['quantity']
        
        # ✅ FIXED: Use retail_price instead of price
        unit_price = float(medicine.retail_price or 0)
        total_price = unit_price * quantity
        
        # Create sale with calculated prices
        sale = Sale.objects.create(
            **validated_data,
            unit_price=unit_price,
            total_price=total_price
        )
        
        # Deduct from stock
        medicine.quantity -= quantity
        medicine.save()
        
        print(f"✅ SALE CREATED: {sale.sale_id} - {medicine.name} x{quantity} = UGX {total_price}")
        print(f"📦 NEW STOCK: {medicine.name} = {medicine.quantity}")
        
        return sale


class MultiItemSaleSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    user = serializers.IntegerField()
    customer_name = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(default='Cash')
    sale_type = serializers.CharField(default='retail')
    
    def create(self, validated_data):
        items = validated_data.pop('items')
        user_id = validated_data.get('user')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        created_sales = []
        total_sale_amount = 0
        
        # Generate a single sale_id for all items
        last_sale = Sale.objects.order_by('-id').first()
        if last_sale and last_sale.sale_id:
            try:
                last_number = int(last_sale.sale_id.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        sale_id = f"SALE-{new_number:06d}"
        
        print(f"🆕 Creating sale with ID: {sale_id}")
        print(f"📦 Items: {len(items)}")
        
        # Create all sale items with the same sale_id
        for item in items:
            medicine_id = item.get('medicine_id')
            quantity = item.get('quantity')
            
            if not medicine_id or not quantity:
                raise serializers.ValidationError("Each item must have medicine_id and quantity")
            
            try:
                medicine = Medicine.objects.get(id=medicine_id)
            except Medicine.DoesNotExist:
                raise serializers.ValidationError(f"Medicine with ID {medicine_id} not found")
            
            # Check stock
            if medicine.quantity < quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock for {medicine.name}. Available: {medicine.quantity}, Requested: {quantity}"
                )
            
            # ✅ FIXED: Use retail_price instead of price
            unit_price = float(medicine.retail_price or 0)
            total_price = unit_price * quantity
            
            # Create sale
            sale = Sale(
                sale_id=sale_id,
                medicine=medicine,
                user=user,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                customer_name=validated_data.get('customer_name', ''),
                notes=validated_data.get('notes', ''),
                payment_method=validated_data.get('payment_method', 'Cash'),
                sale_type=validated_data.get('sale_type', 'retail')
            )
            sale.save()
            
            # ✅ Deduct from stock
            medicine.quantity -= quantity
            medicine.save()
            
            print(f"✅ SOLD: {medicine.name} x{quantity} = UGX {total_price}")
            print(f"📦 NEW STOCK: {medicine.name} = {medicine.quantity}")
            
            created_sales.append(sale)
            total_sale_amount += float(sale.total_price)
        
        # Return the first sale with summary
        result = created_sales[0]
        result.total_sale_amount = total_sale_amount
        result.items_count = len(created_sales)
        
        print(f"💰 TOTAL SALE AMOUNT: UGX {total_sale_amount}")
        
        return result