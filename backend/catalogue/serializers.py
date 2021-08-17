from django.conf import settings
from rest_framework import serializers

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
        min_value=0,
        max_value=settings.BASKET_MAX_QUANTITY_PER_FORM
    )

    class Meta:
        model = catalogue_models.Product
        exclude = ['enable_comment']
        read_only_fields = ['account_name']


def factor_validate(basket, product, quantity):
    if not product.enable_sale:
        raise serializers.ValidationError("Le produit n'est pas disponible à la vente.")

    choices = range(
        1,
        min(
            product.stock,
            settings.BASKET_MAX_QUANTITY_PER_FORM
        ) + 1
    )

    if not min(choices) <= quantity <= max(choices):
        raise serializers.ValidationError(f"La quantité {quantity} n'est pas valide.")

    if len(basket) >= settings.MAX_BASKET_PRODUCT:
        raise serializers.ValidationError(
            f"Nombre maximal ({settings.MAX_BASKET_PRODUCT}) de produits atteint dans le panier."
        )

    return choices


class AddToBasketSerializer(serializers.Serializer):
    product = ProductSerializer(read_only=True)
    basket = serializers.DictField(default={})
    quantity = serializers.IntegerField()

    def validate(self, data):
        choices = factor_validate(data['basket'], self.instance['product'], data['quantity'])

        if bool(data['basket']) and data['basket'].get(self.instance['product'].slug, None) is not None:
            if data['quantity'] + data['basket'][self.instance['product'].slug] > max(choices):
                raise serializers.ValidationError(
                    f"""Votre panier possède déjà {data['basket'][self.instance['product'].slug]} unité(s) 
                    de ce produit, en ajoutant {data['quantity']} vous depassez la limite autorisé."""
                )

        return data


class UpdateBasketSerializer(AddToBasketSerializer):
    id = serializers.IntegerField()
    remove = serializers.BooleanField(default=False)

    def validate(self, data):
        if data['remove']:
            return data

        choices = factor_validate(data['basket'], self.instance[data['id']]['product'], data['quantity'])

        if data['quantity'] > max(choices):
            raise serializers.ValidationError(
                f"Vous depassez la limite autorisé avec cette quantité ({data['quantity']}) demandé."
            )

        return data


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
    basket = serializers.CharField()
    basket_len = serializers.IntegerField()
    price_exact_ttc_with_quantity__sum = serializers.DecimalField(7, 2)
    price_exact_ht_with_quantity__sum = serializers.DecimalField(7, 2)
    deduce_tva = serializers.DecimalField(7, 2)
    price_exact_ht_with_quantity_promo__sum = serializers.DecimalField(7, 2, default=None)
    price_exact_ttc_with_quantity_promo__sum = serializers.DecimalField(7, 2, default=None)
    deduce_tva_promo = serializers.DecimalField(7, 2, default=None)
