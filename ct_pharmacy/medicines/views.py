from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.db import models
from .models import Medicine, Category, Supplier
from .serializers import MedicineSerializer, CategorySerializer, SupplierSerializer

# Class-based views with proper permissions
class MedicineList(generics.ListCreateAPIView):
    queryset = Medicine.objects.all().order_by('-created_at')
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'supplier']
    search_fields = ['name', 'generic_name', 'batch_number']
    ordering_fields = ['name', 'price', 'quantity', 'expiry_date', 'created_at']

class MedicineDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]

class CategoryList(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class SupplierList(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

class SupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

# Function-based views with permission decorators
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def low_stock_medicines(request):
    medicines = Medicine.objects.filter(quantity__lte=models.F('min_stock_level'))
    serializer = MedicineSerializer(medicines, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def expiring_medicines(request):
    thirty_days_later = timezone.now().date() + timedelta(days=30)
    medicines = Medicine.objects.filter(
        expiry_date__lte=thirty_days_later,
        expiry_date__gte=timezone.now().date()
    )
    serializer = MedicineSerializer(medicines, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def expired_medicines(request):
    medicines = Medicine.objects.filter(expiry_date__lt=timezone.now().date())
    serializer = MedicineSerializer(medicines, many=True)
    return Response(serializer.data)