from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Inventory
from .serializers import InventorySerializer

class InventoryAPIViewTest(APITestCase):
    def setUp(self):
        # Create an inventory item for testing
        self.inventory_item = Inventory.objects.create(name="Test Item", stock=10)
        self.inventory_item_url = reverse('inventory-detail', kwargs={'item_id': self.inventory_item.id})

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
        data = {"name": "New Item", "stock": 20}
        response = self.client.post(reverse('inventory-list'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully Inventory created")
        self.assertEqual(Inventory.objects.count(), 2)  # One existing + one created

    def test_create_inventory_item_invalid(self):
        """ Test creating an inventory item with invalid data """
        data = {"name": "", "stock": 20}  # Invalid name
        response = self.client.post(reverse('inventory-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    def test_increase_stock_success(self):
        """ Test increasing the stock of an inventory item """
        data = {"amount": 5}
        response = self.client.put(self.inventory_item_url + '?action=increase', data)
        self.inventory_item.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully increased stock by 5 units.")
        self.assertEqual(self.inventory_item.stock, 15)

    def test_decrease_stock_success(self):
        """ Test decreasing the stock of an inventory item """
        data = {"amount": 3}
        response = self.client.put(self.inventory_item_url + '?action=decrease', data)
        self.inventory_item.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully decreased stock by 3 units.")
        self.assertEqual(self.inventory_item.stock, 7)

    def test_decrease_stock_insufficient(self):
        """ Test decreasing the stock below zero """
        data = {"amount": 15}  # This will fail as it would reduce stock to negative
        response = self.client.put(self.inventory_item_url + '?action=decrease', data)
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
