from rest_framework import serializers
import catalogue.models as catalogue_models
from django.conf import settings


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='catalogue_api:product-list-category',
        lookup_field='slug'
    )
    products_count__sum = serializers.IntegerField(default=None)

    class Meta:
        model = catalogue_models.Category
        fields = ['url', 'category', 'slug', 'products_count__sum']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = catalogue_models.ProductImage
        fields = ['image']


class ProductSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='catalogue_api:product-detail',
        lookup_field='pk'
    )
    productimage_set = ProductImageSerializer(many=True)
    categories = CategorySerializer(many=True)
    price_exact_ttc = serializers.DecimalField(7, 2)
    price_exact_ht = serializers.DecimalField(7, 2)
    price_base_ttc = serializers.DecimalField(7, 2)
    effective_reduction = serializers.IntegerField(min_value=0, max_value=100)
    effective_basket_quantity = serializers.IntegerField(
        min_value=0, max_value=settings.BASKET_MAX_QUANTITY_PER_FORM)

    class Meta:
        model = catalogue_models.Product
        exclude = ['enable_comment']


class FilterAnnotatedSerializer(serializers.Serializer):
    open = serializers.BooleanField()
    close = serializers.ListField()
    level = serializers.IntegerField()


class CatalogueFilterAnnotatedSerializer(serializers.Serializer):
    category = serializers.SerializerMethodField()
    annotation = serializers.SerializerMethodField()

    def get_category(self, data_tuple):
        return CategorySerializer(
            data_tuple[0],
            context={'request': self.context['request']}
        ).data

    def get_annotation(self, data_tuple):
        return FilterAnnotatedSerializer(data_tuple[1]).data


class CatalogueSerializer(serializers.Serializer):
    related_products = ProductSerializer(many=True)
    price_exact_ttc__min = serializers.DecimalField(7, 2)
    price_exact_ttc__max = serializers.DecimalField(7, 2)
    order = serializers.IntegerField(min_value=-1, max_value=1)
    index = serializers.CharField()
    selected_category = CategorySerializer()
    selected_category_root = CategorySerializer()
    filled_category = CategorySerializer(many=True)

    filter_list = CatalogueFilterAnnotatedSerializer(many=True)
