from django.conf import settings
from rest_framework import serializers, fields

import catalogue.models as catalogue_models
import sale.models as sale_models


class CategoryDumpSerializer(serializers.Serializer):
    category = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    def get_category(self, ret):
        return ret['category'].data

    def get_children(self, ret):
        child = ret.get('children', None)
        if child is None:
            return None

        return CategoryDumpSerializer(child, many=True).data


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='catalogue_api:product-list-category',
        lookup_field='slug',
        lookup_url_kwarg='slug_category'
    )
    products_count__sum = serializers.IntegerField(default=None)
    path = serializers.CharField()

    @classmethod
    def MP_Node_dump_bulk_drf(cls, request, parent=None, annotates=None, depth_lte=None):
        """Dumps a tree branch to a python data structure."""

        # Because of fix_tree, this method assumes that the depth
        # and numchild properties in the nodes can be incorrect,
        # so no helper methods are used
        if annotates is None:
            annotates = {}
        qset = cls.Meta.model.objects.all()
        if parent:
            qset = qset.filter(path__startswith=parent.path,
                               depth__gte=parent.depth)

        if depth_lte is not None:
            qset = qset.filter(
                depth__lte=depth_lte
            )

        ret, lnk = [], {}

        if bool(annotates):
            qset = qset.annotate(**annotates)

        for obj in qset:
            newobj = {
                cls.Meta.model.__name__.lower(): cls(
                    obj, context={'request': request})
            }

            path = obj.path
            depth = int(len(path) / cls.Meta.model.steplen)

            if (not parent and depth == 1) or \
                    (parent and len(path) == len(parent.path)):
                ret.append(newobj)
            else:
                parentpath = cls.Meta.model._get_basepath(path, depth - 1)
                parentobj = lnk[parentpath]
                if 'children' not in parentobj:
                    parentobj['children'] = []
                parentobj['children'].append(newobj)
            lnk[path] = newobj
        return ret

    class Meta:
        model = catalogue_models.Category
        fields = ['url', 'category', 'slug', 'path', 'products_count__sum']


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
        min_value=0, max_value=settings.BASKET_MAX_QUANTITY_PER_FORM
    )

    def __init__(self, instance=None, data=fields.empty, **kwargs):
        self.basket = {}
        self.choices = range(1, settings.BASKET_MAX_QUANTITY_PER_FORM + 1)

        if isinstance(data, dict):
            self.basket = data.get(settings.BASKET_SESSION_KEY, {})

            if bool(self.basket):
                data = data.copy()
                del data[settings.BASKET_SESSION_KEY]

        super(ProductSerializer, self).__init__(
            instance=instance, data=data, **kwargs
        )

        for field in self.fields:
            if field != 'quantity':
                self.fields[field].read_only = True

        if instance is not None:
            try:
                self.choices = range(
                    1,
                    min(
                        instance.stock,
                        settings.BASKET_MAX_QUANTITY_PER_FORM
                    ) + 1
                )
                self.fields['quantity'] = serializers.ChoiceField(
                    source="stock",
                    choices=self.choices
                )
            except KeyError:
                pass

    def validate(self, data):
        quantity = data['stock']

        if not self.instance.enable_sale:
            raise serializers.ValidationError("Le produit n'est pas disponible à la vente.")

        if len(self.basket) >= settings.MAX_BASKET_PRODUCT:
            raise serializers.ValidationError(
                f"Nombre maximal ({settings.MAX_BASKET_PRODUCT}) de produits atteint dans le panier."
            )

        if bool(self.basket) and self.basket.get(self.instance.slug, None) is not None:
            if quantity + self.basket[self.instance.slug] > max(self.choices):
                raise serializers.ValidationError(
                    f"""Votre panier possède déjà {self.basket[self.instance.slug]} unité(s) 
                    de ce produit, en ajoutant {quantity} vous depassez la limite autorisé."""
                )

        return data

    class Meta:
        model = catalogue_models.Product
        exclude = ['enable_comment']
        read_only_fields = ['account_name']


class BasketProductSerializer(ProductSerializer):
    price_exact_ttc_with_quantity = serializers.DecimalField(7, 2)
    price_exact_ht_with_quantity = serializers.DecimalField(7, 2)


class FilterAnnotatedSerializer(serializers.Serializer):
    open = serializers.BooleanField()
    close = serializers.ListField()
    level = serializers.IntegerField()


class CatalogueSerializer(serializers.Serializer):
    related_products = ProductSerializer(many=True)
    price_exact_ttc__min = serializers.DecimalField(7, 2)
    price_exact_ttc__max = serializers.DecimalField(7, 2)
    order = serializers.CharField()
    index = serializers.CharField()
    selected_category = CategorySerializer()
    selected_category_root = CategorySerializer()
    filled_category = CategorySerializer(many=True)
    filter_list = CategoryDumpSerializer(many=True)


class PromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = sale_models.Promo
        fields = ('code', 'type', 'value')


class BasketSurfaceSerializer(serializers.Serializer):
    products = BasketProductSerializer(many=True)
    promo = PromoSerializer()
    basket_sign = serializers.CharField()
    price_exact_ttc_with_quantity__sum = serializers.DecimalField(7, 2)
    price_exact_ht_with_quantity__sum = serializers.DecimalField(7, 2)
    deduce_tva = serializers.DecimalField(7, 2)
    price_exact_ht_with_quantity_promo__sum = serializers.DecimalField(7, 2, default=None)
    price_exact_ttc_with_quantity_promo__sum = serializers.DecimalField(7, 2, default=None)
    deduce_tva_promo = serializers.DecimalField(7, 2, default=None)
