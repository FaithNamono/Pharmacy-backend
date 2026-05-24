from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from .models import Prescription, PrescriptionItem
from .serializers import PrescriptionSerializer, PrescriptionItemSerializer, FillPrescriptionSerializer
from ct_pharmacy.medicines.models import Medicine
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
import json

class PrescriptionList(generics.ListCreateAPIView):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Add this

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        # Handle image from multipart form data
        prescription_image = self.request.FILES.get('prescription_image')
        
        prescription = serializer.save(
            created_by=self.request.user,
            prescription_image=prescription_image
        )
        
        # Parse items - could be in request.data or request.POST
        items_data = self.request.data.get('items', [])
        if isinstance(items_data, str):
            import json
            items_data = json.loads(items_data)
        
        for item_data in items_data:
            PrescriptionItem.objects.create(
                prescription=prescription,
                medicine_id=item_data.get('medicine'),
                prescribed_quantity=item_data.get('prescribed_quantity'),
                dosage_instructions=item_data.get('dosage_instructions', ''),
                duration=item_data.get('duration', '')
            )

class PrescriptionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def fill_prescription(request, pk):
    try:
        prescription = Prescription.objects.get(pk=pk)
    except Prescription.DoesNotExist:
        return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if prescription.is_expired:
        return Response({'error': 'Prescription has expired'}, status=status.HTTP_400_BAD_REQUEST)
    
    filled_items = request.data.get('items', [])
    filled_notes = request.data.get('notes', '')
    
    if not filled_items:
        return Response({'error': 'No items to fill'}, status=status.HTTP_400_BAD_REQUEST)
    
    results = []
    errors = []
    
    for item_data in filled_items:
        item_id = item_data.get('item_id')
        quantity = item_data.get('quantity_filled')
        
        try:
            item = PrescriptionItem.objects.get(id=item_id, prescription=prescription)
        except PrescriptionItem.DoesNotExist:
            errors.append(f"Item {item_id} not found")
            continue
        
        remaining = item.prescribed_quantity - item.filled_quantity
        
        if quantity > remaining:
            errors.append(f"Quantity {quantity} exceeds remaining {remaining} for {item.medicine.name}")
            continue
        
        # Check stock
        if item.medicine.quantity < quantity:
            errors.append(f"Insufficient stock for {item.medicine.name}. Available: {item.medicine.quantity}")
            continue
        
        # Update stock
        item.medicine.quantity -= quantity
        item.medicine.save()
        
        # Update item
        item.filled_quantity += quantity
        item.save()
        
        results.append({
            'item_id': item.id,
            'medicine': item.medicine.name,
            'filled': quantity,
            'remaining': item.remaining_quantity
        })
    
    # Update prescription status
    all_fully_filled = all(item.is_fully_filled for item in prescription.items.all())
    any_filled = any(item.filled_quantity > 0 for item in prescription.items.all())
    
    if all_fully_filled:
        prescription.status = 'filled'
    elif any_filled:
        prescription.status = 'partially_filled'
    
    if filled_notes:
        prescription.notes = f"{prescription.notes}\n{filled_notes}"
    
    prescription.save()
    
    return Response({
        'prescription_id': prescription.prescription_id,
        'status': prescription.status,
        'results': results,
        'errors': errors
    })        