from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Product, ProductVariant
from .serializers import ProductSerializer, CategorySerializer, ProductVariantListSerializer, ProductVariantDetailSerializer


class CategoryCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = CategorySerializer(data=request.data)

        if serializer.is_valid():
            category = serializer.save()
            return Response(
                CategorySerializer(category).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProductCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Wrap in a transaction so if variant creation fails, 
                # the product isn't created either (Atomic)
                with transaction.atomic():
                    serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, slug):
        product = get_object_or_404(Product.all_objects, slug=slug)
        serializer = ProductSerializer(product, data=request.data, partial=True)

        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VariantListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        variants = ProductVariant.objects.filter(
            is_active=True,
            product__is_active=True
        ).select_related("product")

        serializer = ProductVariantListSerializer(variants, many=True)
        return Response(serializer.data)

class VariantDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, sku):
        variant = get_object_or_404(
            ProductVariant.objects.select_related("product"),
            sku=sku,
            is_active=True,
            product__is_active=True
        )
        serializer = ProductVariantDetailSerializer(variant)
        return Response(serializer.data)

