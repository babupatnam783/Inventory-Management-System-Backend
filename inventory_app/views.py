from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
#models

from .models import Product as ProductModel
from .models import Inventory

#serializers
from .serializers import CategorySerializer,ProductSerializer,InventorySerializer

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


from django.shortcuts import get_object_or_404
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

#cache
from django.core.cache import cache


# Create your views here.
class ProductAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,product_id = None):
        if product_id:
            cache_key = f'product_{product_id}'
            cached_product = cache.get(cache_key)
            print(cached_product)
            if cached_product:
                print("redis")
                return Response(cached_product, status=status.HTTP_200_OK)

            product = get_object_or_404(ProductModel, id=product_id)
            serializer = ProductSerializer(product)

            cache.set(cache_key, serializer.data, timeout=60*15)

            return Response(serializer.data, status=status.HTTP_200_OK)
    
        products = ProductModel.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self,request,):
        data = request.data
        serializer = ProductSerializer(data = data)
        if not serializer.is_valid():
            return Response({"message":serializer.errors}, status=400)

        product = serializer.save()
        cache_key = f'product_{product.id}'
        cache.delete(cache_key)

        return Response({"message": "Successfully Product created","data":serializer.data}, status=201)

    def put(self,request, product_id=None):
        if not product_id:
            return Response({"error": " Product Id is required for updating."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        oProduct = ProductModel.objects.get(id = product_id)
        serializer = ProductSerializer(oProduct,data = data, partial = True)
        if not serializer.is_valid():
            return Response({"message":serializer.errors}, status=400)

        product = serializer.save()
        cache_key = f'product_{product.id}'
        cache.delete(cache_key)

        cache.set(cache_key, serializer.data, timeout=60*15) # Cache for 15 minutes

        return Response({"message": f"Product Id {product_id} updated"}, status=201)

    def delete(self,request, product_id=None):
        if not product_id:
            return Response({"error": " Product Id is required for deleting."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(ProductModel, id=product_id)
        product.delete()
        cache_key = f'product_{product_id}'
        cache.delete(cache_key)

        return Response({"message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class InventoryAPIView(APIView):
    def get(self, request, item_id = None):
        if not item_id:
            return Response({"error": "Item ID is required for getting."}, status=status.HTTP_400_BAD_REQUEST)

        # Try to fetch from cache
        cache_key = f'inventory_{item_id}'
        cached_inventory = cache.get(cache_key)
        print("cached_inv",cached_inventory)

        if cached_inventory:
            return Response(cached_inventory, status=status.HTTP_200_OK)

        try:
            oInventory = Inventory.objects.get(id = item_id)
            serializer = InventorySerializer(oInventory)
            cache.set(cache_key, serializer.data, timeout=60*15) # Cache for 15 minutes
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Inventory.DoesNotExist:
            return Response({"error": "Inventory item not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self,request,):
        data = request.data
        serializer = InventorySerializer(data = data)
        if not serializer.is_valid():
            return Response({"message":serializer.errors}, status=400)

        inventory = serializer.save()
        cache_key = f'inventory_{inventory.id}'
        cache.delete(cache_key)
        return Response({"message": "Successfully Inventory created","data":serializer.data}, status=status.HTTP_200_OK)

    def put(self,request, item_id = None,action = None):

        if not item_id or action not in ['increase', 'decrease']:
            return Response({"error": "Invalid request. Provide both item_id and action ('increase' or 'decrease')."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not item_id:
            return Response({"error": "Item ID is required for updating."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = request.data
            oInventory = Inventory.objects.get(id = item_id)
            amount = request.data.get('amount', 0)

            if not isinstance(amount, int) or amount <= 0:
                return Response({"error": "Please provide a valid positive integer amount."}, 
                            status=status.HTTP_400_BAD_REQUEST)
            if action == 'increase':
                oInventory.increase_stock(amount)
                return Response({"message": f"Successfully increased stock by {amount} units."}, status=status.HTTP_200_OK)
            elif action == 'decrease':
                try:
                    oInventory.decrease_stock(amount)
                    return Response({"message": f"Successfully decreased stock by {amount} units."}, status=status.HTTP_200_OK)
                except ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Inventory.DoesNotExist:
            return Response({"error": "Inventory item not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self,request, item_id=None):
        if not item_id:
            return Response({"error": "Item ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            oInventory = Inventory.objects.get(id=item_id)
            oInventory.delete()

            cache_key = f'inventory_{item_id}'
            cache.delete(cache_key)

            return Response({"message": f"Inventory {item_id} successfully deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Inventory.DoesNotExist:
            return Response({"error": "Inventory item not found."}, status=status.HTTP_404_NOT_FOUND)