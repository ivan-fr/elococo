from django.conf import settings
from rest_framework import serializers
from rest_framework.fields import empty

from catalogue.models import Product, Category, ProductToProduct, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        exclude = ('product',)


class ProductElementSerializer(serializers.ModelSerializer):
    productimage_set = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        exclude = ('subproducts', 'categories')


class ProductToProductSerializer(serializers.ModelSerializer):
    elements = ProductElementSerializer()

    class Meta:
        model = ProductToProduct
        exclude = ('box',)


class ProductSerializer(serializers.ModelSerializer):
    productimage_set = ProductImageSerializer(many=True, read_only=True)
    box = ProductToProductSerializer(many=True, read_only=True)
    post_effective_stock_with_basket = serializers.IntegerField(read_only=True)
    quantity_from_basket_box = serializers.IntegerField(read_only=True)
    price_exact_ttc = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    price_exact_ht = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    price_base_ttc = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    effective_reduction = serializers.IntegerField(read_only=True)
    effective_stock = serializers.IntegerField(read_only=True)
    stock_sold = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        exclude = ('subproducts',)
        depth = 1


class ProductBasketSerializer(ProductSerializer):
    post_effective_basket_quantity = serializers.IntegerField(
        read_only=True
    )
    price_exact_ttc_with_quantity = serializers.DecimalField(
        read_only=True, max_digits=7, decimal_places=2
    )
    price_exact_ht_with_quantity = serializers.DecimalField(
        read_only=True, max_digits=7, decimal_places=2
    )
    to_delete = serializers.BooleanField(default=False)
    choices = tuple(range(1, settings.BASKET_MAX_QUANTITY_PER_FORM + 1))
    to_quantity = serializers.ChoiceField(choices=[(i, i) for i in choices])

    def __init__(self, instance=None, data=empty, **kwargs):
        super(ProductBasketSerializer, self).__init__(instance, data=data, **kwargs)

        try:
            self.choices = range(
                1,
                min(
                    instance["product"].post_effective_stock_with_basket,
                    settings.BASKET_MAX_QUANTITY_PER_FORM
                ) + 1
            )
            self.fields["to_quantity"].choices = [(i, i) for i in self.choices]
            self.fields["to_quantity"].default = max(self.choices)
        except KeyError:
            pass

    def validate(self, attrs):
        basket = self.context["request"].session.get(settings.BASKET_SESSION_KEY, {})
        product = self.instance["product"]
        factor_clean(self.instance["product"], basket)

        if bool(basket) and basket.get(product.slug, None) is not None:
            if attrs["to_quantity"] > max(self.choices):
                raise serializers.ValidationError(
                    f"""Vous depassez la limite autorisé avec cette quantité 
                    ({attrs['to_quantity']}) demandé."""
                )

        return attrs

    class Meta(ProductSerializer.Meta):
        pass


class ShopSerializer(serializers.Serializer):
    related_products = ProductSerializer(many=True, read_only=True)
    filled_category = CategorySerializer(many=True, read_only=True)
    selected_category_root = CategorySerializer(read_only=True)
    selected_category = CategorySerializer(read_only=True)
    filter_list = serializers.SerializerMethodField(read_only=True)

    def get_filter_list(self, dict_):
        if dict_["filter_list"] is None:
            return None
        return ((CategorySerializer(instance=subT[0]).data, subT[1]) for subT in dict_["filter_list"])


def factor_clean(product_instance, basket):
    if product_instance is None:
        raise serializers.ValidationError(
            "Le produit n'existe pas."
        )

    if not product_instance.enable_sale:
        raise serializers.ValidationError(
            "Le produit n'est pas disponible à la vente."
        )

    if len(basket) >= settings.MAX_BASKET_PRODUCT:
        raise serializers.ValidationError(
            f"Nombre maximal ({settings.MAX_BASKET_PRODUCT}) de produits atteint dans le panier."
        )


class BasketSerializer(serializers.Serializer):
    products = ProductBasketSerializer(many=True)
    price_exact_ttc_with_quantity__sum = serializers.DecimalField(read_only=True, max_digits=7, decimal_places=2)
    price_exact_ht_with_quantity__sum = serializers.DecimalField(read_only=True, max_digits=7, decimal_places=2)
    price_exact_ht_with_quantity_promo__sum = serializers.DecimalField(read_only=True, max_digits=7, decimal_places=2)
    price_exact_ttc_with_quantity_promo__sum = serializers.DecimalField(read_only=True, max_digits=7, decimal_places=2)


class ShopDetailSerializer(serializers.Serializer):
    product = ProductSerializer(read_only=True)
    choices = tuple(range(1, settings.BASKET_MAX_QUANTITY_PER_FORM + 1))
    quantity = serializers.ChoiceField(choices=[(i, i) for i in choices], default=min(choices))

    def __init__(self, instance=None, data=empty, **kwargs):
        super(ShopDetailSerializer, self).__init__(instance, data=data, **kwargs)

        if instance["product"] is not None:
            try:
                self.choices = range(
                    1,
                    min(
                        instance["product"].post_effective_stock_with_basket,
                        settings.BASKET_MAX_QUANTITY_PER_FORM
                    ) + 1
                )
                self.fields["quantity"].choices = ((i, i) for i in self.choices)
                self.fields["quantity"].default = max(self.choices)
            except KeyError:
                pass

    def validate(self, attrs):
        basket = self.context["request"].session.get(settings.BASKET_SESSION_KEY, {})
        product = self.instance["product"]
        factor_clean(self.instance["product"], basket)

        if bool(basket) and basket.get(product.slug, None) is not None:
            if attrs["quantity"] + basket[product.slug]["quantity"] > max(self.choices):
                raise serializers.ValidationError(
                    f"""Votre panier possède déjà {basket[product.slug]["quantity"]} quantité 
                    de ce produit, en ajoutant {attrs["quantity"]} vous depassez la limite autorisé."""
                )

        return attrs
