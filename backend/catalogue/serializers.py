from rest_framework import serializers
import catalogue.models as catalogue_models
from django.conf import settings


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = catalogue_models.Category
        fields = ['category', 'slug']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = catalogue_models.ProductImage
        fields = ['image']


class ProductSerializer(serializers.ModelSerializer):
    productimage_set = ProductImageSerializer(many=True)
    categories = CategorySerializer(many=True)
    price_exact_ttc = serializers.DecimalField(7, 2)
    price_exact_ht = serializers.DecimalField(7, 2)
    price_base_ttc = serializers.DecimalField(7, 2)
    effective_reduction = serializers.IntegerField(min_value=0, max_value=100)
    effective_basket_quantity = serializers.IntegerField(min_value=0, max_value=settings.BASKET_MAX_QUANTITY_PER_FORM)

    class Meta:
        model = catalogue_models.Product
        exclude = ['enable_comment']


class CatalogueSerializer(serializers.Serializer):
    related_products = ProductSerializer(many=True)
    price_exact_ttc__min = serializers.DecimalField(7, 2)
    price_exact_ttc__max = serializers.DecimalField(7, 2)
    order = serializers.IntegerField(min_value=-1, max_value=1)
    index = serializers.CharField()
    selected_category = CategorySerializer()
    selected_category_root = CategorySerializer()
    filled_category = CategorySerializer(many=True)
