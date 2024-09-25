from .models import Category,Product,Inventory
from rest_framework import serializers

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', required=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'category_name', 'description', 'price', 'created_at', 'updated_at']

    def create(self, validated_data):
        category_name = validated_data.pop('category')['name']

        # Try to retrieve the category by name
        category, created = Category.objects.get_or_create(name=category_name)  # Creates the category if it doesn't exist

        product = Product.objects.create(category=category, **validated_data)
        return product

class InventorySerializer(serializers.ModelSerializer):
    # product = ProductSerializer()
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'product','product_name', 'quantity']
       