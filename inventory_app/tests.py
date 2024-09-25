from django.test import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.cache import cache
from .models import Product,Category, Inventory
from .serializers import ProductSerializer, InventorySerializer

class ProductAPITest(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Laptop",
            category=self.category,
            description="A gaming laptop",
            price=1200.00
        )
        self.valid_product_data = {
            "name": "Updated Laptop",
            "description": "Updated description",
            "price": "1500.00"
        }
        
        self.invalid_product_data = {
            "name": "",  # Name is required
            "category": self.category.id,
            "description": "Updated description",
            "price": "1500.00"
        }
        self.product_url = reverse('product-detail', kwargs={'product_id': self.product.id})
        self.products_list_url = reverse('product-list')

    def tearDown(self):
        cache.clear()

    def test_get_product_success(self):
        """ Test retrieving a single product by its ID """
        response = self.client.get(self.product_url)
        product = Product.objects.get(id=self.product.id)
        serializer = ProductSerializer(product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_product_not_found(self):
        """ Test retrieving a non-existent product """
        invalid_product_url = reverse('product-detail', kwargs={'product_id': 9999})
        response = self.client.get(invalid_product_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_all_products(self):
        """ Test retrieving all products """
        response = self.client.get(self.products_list_url)
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_product_cached(self):
        """ Test retrieving a product from the cache """
        cache_key = f'product_{self.product.id}'
        serializer = ProductSerializer(self.product).data
        cache.set(cache_key, serializer, timeout=60*15)

        response = self.client.get(self.product_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer)
        # self.assertContains(response, "redis")

    def test_post_product_success(self):
        """ Test creating a new product """
        new_product_data = {
            "name": "Smartphone",
            "category_name": self.category.name,
            "description": "A high-end smartphone",
            "price": "800.00"
        }
        response = self.client.post(self.products_list_url, new_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_post_product_invalid(self):
        """ Test creating a product with invalid data """
        response = self.client.post(self.products_list_url, self.invalid_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Product.objects.count(), 1)

    def test_put_product_success(self):
        """ Test updating an existing product """
        response = self.client.put(self.product_url, self.valid_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, self.valid_product_data['name'])
        self.assertEqual(self.product.description, self.valid_product_data['description'])
        self.assertEqual(float(self.product.price), float(self.valid_product_data['price']))

    def test_put_product_invalid(self):
        """ Test updating a product with invalid data """
        response = self.client.put(self.product_url, self.invalid_product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_delete_product_success(self):
        """ Test deleting a product """
        response = self.client.delete(self.product_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)

    def test_cache_invalidation_after_delete(self):
        """ Test that cache is invalidated after deleting a product """
        cache_key = f'product_{self.product.id}'
        cache.set(cache_key, ProductSerializer(self.product).data, timeout=60*15)

        response = self.client.delete(self.product_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(cache.get(cache_key))


class InventoryAPIViewTest(APITestCase):
    def setUp(self):
        # Create an inventory item for testing
        self.category = Category.objects.create(name="Test")
        self.product = Product.objects.create(name="Test Product", description="A test product",category=self.category, price=100.00)
        self.inventory_item = Inventory.objects.create( product=self.product, quantity=10)
        self.inventory_item_url = reverse('inventory-detail', kwargs={'item_id': self.inventory_item.id})
        self.inventory_item_url_increase = reverse('inventory-detail', kwargs={'item_id': self.inventory_item.id,"action":"increase"})
        self.inventory_item_url_decrease = reverse('inventory-detail', kwargs={'item_id': self.inventory_item.id,"action":"decrease"})


    def test_get_inventory_item_success(self):
        """ Test retrieving an inventory item by ID """
        response = self.client.get(self.inventory_item_url)
        serializer = InventorySerializer(self.inventory_item)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_inventory_item_not_found(self):
        """ Test retrieving an inventory item that does not exist """
        response = self.client.get(reverse('inventory-detail', kwargs={'item_id': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Inventory item not found."})

    def test_create_inventory_item_success(self):
        """ Test creating a new inventory item """
        data = {"product": self.product.id, "quantity": 20}
        response = self.client.post(reverse('inventory'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully Inventory created")
        self.assertEqual(Inventory.objects.count(), 2)  # One existing + one created

    def test_create_inventory_item_invalid(self):
        """ Test creating an inventory item with invalid data """
        data = {"product": self.product.id, "quantity": -5} 
        response = self.client.post(reverse('inventory'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    def test_increase_stock_success(self):
        """ Test increasing the stock of an inventory item """
        data = {"amount": 5}
        response = self.client.put(f"{self.inventory_item_url}?action=increase", data)
        self.inventory_item.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully increased stock by 5 units.")
        self.assertEqual(self.inventory_item.stock, 15)

    def test_decrease_stock_success(self):
        """ Test decreasing the stock of an inventory item """
        data = {"amount": 3}
        response = self.client.put(f"{self.inventory_item_url}?action=decrease", data)
        self.inventory_item.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully decreased stock by 3 units.")
        self.assertEqual(self.inventory_item.stock, 7)

    def test_decrease_stock_insufficient(self):
        """ Test decreasing the stock below zero """
        data = {"amount": 15}  # This will fail as it would reduce stock to negative
        response = self.client.put(f"{self.inventory_item_url}?action=decrease", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_delete_inventory_item_success(self):
        """ Test deleting an inventory item """
        response = self.client.delete(self.inventory_item_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Inventory.objects.count(), 0)

    def test_delete_inventory_item_not_found(self):
        """ Test deleting an inventory item that does not exist """
        response = self.client.delete(reverse('inventory-detail', kwargs={'item_id': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Inventory item not found."})
