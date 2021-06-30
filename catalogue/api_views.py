from operator import methodcaller

from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from catalogue.bdd_calculations import (
    price_annotation_format, annotate_effective_stock, get_quantity_from_basket_box, get_stock_with_basket,
    filled_category, post_effective_basket_quantity, post_price_annotation_format, total_price_from_all_product)
from catalogue.models import Product
from catalogue.serializers import ShopSerializer, ShopDetailSerializer, BasketSerializer
from sale.bdd_calculations import get_promo


def update_basket_session(session, serializer, set_quantity=False):
    product = serializer.data["product"]

    if serializer.validated_data.get("remove", False):
        if session.get(settings.BASKET_SESSION_KEY, None) is None:
            return
        del session[settings.BASKET_SESSION_KEY][product["slug"]]
        session.modified = True
        return

    if set_quantity:
        if session[settings.BASKET_SESSION_KEY].get(product["slug"], None) is not None:
            session[settings.BASKET_SESSION_KEY][product["slug"]]["quantity"] = serializer.validated_data["quantity"]
            session.modified = True
        return

    if session.get(settings.BASKET_SESSION_KEY, None) is None:
        session[settings.BASKET_SESSION_KEY] = {
            product["slug"]: {
                "product_name": product["name"],
                "quantity": serializer.validated_data["quantity"]
            }
        }
    else:
        if session[settings.BASKET_SESSION_KEY].get(product["slug"], None) is not None:
            session[settings.BASKET_SESSION_KEY][product["slug"]]["quantity"] = \
                session[settings.BASKET_SESSION_KEY][product["slug"]]["quantity"] + \
                serializer.validated_data["quantity"]
        else:
            session[settings.BASKET_SESSION_KEY][product["slug"]] = {
                "product_name": product["name"],
                "quantity": serializer.validated_data["quantity"]
            }
        session.modified = True


class BasketViewSet(viewsets.ViewSet):
    def get_queryset(self):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        return Product.objects.filter(
            enable_sale=True
        ).annotate(
            **annotate_effective_stock()
        ).filter(
            effective_stock__gt=0
        ).filter(
            slug__in=tuple(basket.keys())
        ).annotate(
            **price_annotation_format(basket)
        ).annotate(
            **get_quantity_from_basket_box(basket)
        ).annotate(
            **post_effective_basket_quantity(), **get_stock_with_basket()
        ).annotate(
            **post_price_annotation_format()
        ).filter(
            post_effective_basket_quantity__gte=0
        )

    def get_object_list(self, queryset):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        object_list = queryset.all()
        basket_set = {product_slug for product_slug in basket.keys()}
        product_bdd_set = {product.slug for product in queryset}

        product_to_delete = basket_set.difference(product_bdd_set)

        if len(product_to_delete) > 0:
            for product_slug in product_to_delete:
                del basket[product_slug]
            self.request.session[settings.BASKET_SESSION_KEY] = basket
            self.request.session.modified = True

        for product in object_list:
            if product.post_effective_basket_quantity != basket[product.slug]["quantity"]:
                basket[product.slug]["quantity"] = product.post_effective_basket_quantity
                self.request.session.modified = True

        object_list = filter(
            lambda product_filter: product_filter.slug not in product_to_delete,
            object_list
        )

        basket_enum = {product_slug: n for n, product_slug in enumerate(basket.keys())}
        return sorted(
            object_list, key=methodcaller('compute_basket_oder', basket_enum=basket_enum)
        ), product_to_delete

    def list(self, request):
        queryset = self.get_queryset()
        object_list, product_to_delete = self.get_object_list(queryset)
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})
        promo_session = self.request.session.get(settings.PROMO_SESSION_KEY, {})
        promo = get_promo(basket, promo_session.get("code_promo", None))

        if promo is None and self.request.session.get(settings.PROMO_SESSION_KEY, None) is not None:
            del self.request.session[settings.PROMO_SESSION_KEY]

        data = queryset.exclude(
            slug__in=product_to_delete
        ).aggregate(
            **total_price_from_all_product(promo=promo)
        )

        data["products"] = object_list

        serializer = BasketSerializer(data, context={"request": request})
        return Response(serializer.data)


class ShopViewSet(viewsets.ViewSet):
    def get_queryset(self):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        return Product.objects.prefetch_related(
            'categories',
            "productimage_set",
            'box',
            'box__elements',
            "box__elements__productimage_set"
        ).annotate(
            **annotate_effective_stock()
        ).annotate(
            **price_annotation_format(basket)
        ).annotate(
            **get_quantity_from_basket_box(basket)
        ).annotate(
            **get_stock_with_basket()
        )

    def list(self, request):
        queryset = self.get_queryset()
        data = filled_category(5)
        data["related_products"] = queryset

        serializer = ShopSerializer(data, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, url_path=r"category/(?P<category_slug>[-\w]+)")
    def category(self, _, category_slug):
        queryset = self.get_queryset()
        data = filled_category(5, category_slug, queryset)
        serializer = ShopSerializer(data)
        return Response(serializer.data)

    def update(self, request, pk=None):
        try:
            product = self.get_queryset().filter(
                pk=pk
            ).get()
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = {
            "product": product,
        }

        serializer = ShopDetailSerializer(
            data,
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            update_basket_session(self.request.session, serializer)
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def retrieve(self, request, pk=None):
        try:
            product = self.get_queryset().filter(
                pk=pk
            ).get()
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = {
            "product": product,
        }

        serializer = ShopDetailSerializer(
            data,
            context={"request": request}
        )

        return Response(serializer.data)
