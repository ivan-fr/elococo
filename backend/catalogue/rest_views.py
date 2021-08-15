import re
from decimal import Decimal
from operator import methodcaller

from django.conf import settings
from django.core import signing
from django.core.signing import Signer
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

import catalogue.models as catalogue_models
import catalogue.serializers as catalogue_serializers
from catalogue.bdd_calculations import (
    cast_annotate_to_float, data_from_all_product, filled_category, price_annotation_format,
    total_price_from_all_product, post_price_annotation_format)
from sale.bdd_calculations import get_promo


def update_basket(basket, slug, type_=None, quantity=0):
    if type_ == "remove":
        if basket.get(slug, None) is not None:
            del basket[slug]
        return

    if type_ == "set_quantity":
        if basket.get(slug, None) is not None:
            basket[slug] = quantity
        return

    if not bool(basket):
        basket[slug] = quantity
    else:
        if basket.get(slug, None) is not None:
            basket[slug] += quantity
        else:
            basket[slug] = quantity


def get_basket(signer, data_to_unsign):
    try:
        return signer.unsign_object(data_to_unsign)
    except signing.BadSignature:
        return {}
    except TypeError:
        return {}
    except KeyError:
        return {}
    except AttributeError:
        return {}


def product_to_exclude_(products, basket):
    basket_set = {product_slug for product_slug in basket.keys()}
    product_bdd_set = {product.slug for product in products}

    product_to_exclude = basket_set.difference(product_bdd_set)

    if len(product_to_exclude) > 0:
        for product_slug in product_to_exclude:
            del basket[product_slug]

    for product in products:
        if product.effective_basket_quantity != basket[product.slug]:
            basket[product.slug] = product.effective_basket_quantity

    products = filter(
        lambda product_filter: product_filter.slug not in product_to_exclude, products
    )

    basket_enum = {product_slug: n for n, product_slug in enumerate(basket.keys())}

    return sorted(
        products, key=methodcaller('compute_basket_oder', basket_enum=basket_enum)
    ), product_to_exclude, basket_enum


def get_basket_len(basket):
    return {"basket_len": sum((quantity for quantity in basket.values()))}


class CatalogueViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = catalogue_models.Product.enable_objects.prefetch_related(
        "productimage_set", "categories"
    )
    serializer_class = catalogue_serializers.ProductSerializer
    ordering = None

    def list_catalogue(self, request, **kwargs):
        self.serializer_class = catalogue_serializers.CatalogueSerializer

        dict_data = filled_category(5, kwargs.get(
            'slug_category', None), products_queryset=self.queryset,
                                    dump=True, request=request)
        dict_data.update({"index": None})

        selected_category_root = dict_data.get("selected_category_root", None)

        if selected_category_root is not None:
            dict_data.update({"index": selected_category_root.slug})

        if dict_data.get("related_products", None) is not None:
            self.queryset = dict_data["related_products"]
            dict_data["related_products"] = None

        annotation_p = price_annotation_format()
        cast_annotate_to_float(annotation_p, "price_exact_ttc")

        self.queryset = self.queryset.annotate(**annotation_p)
        dict_data.update(self.queryset.aggregate(*data_from_all_product()))

        try:

            min_ttc_price = request.GET.get("min_ttc_price", None)
            max_ttc_price = request.GET.get("max_ttc_price", None)

            try:
                _ = min_ttc_price[8], max_ttc_price[8]
                raise TypeError()
            except IndexError:
                if min_ttc_price == 'NaN' or max_ttc_price == 'Nan':
                    raise TypeError()
                min_ttc_price = float(min_ttc_price)
                max_ttc_price = float(max_ttc_price)

            if min_ttc_price is not None and max_ttc_price is not None:
                if min_ttc_price < dict_data['price_exact_ttc__min']:
                    min_ttc_price = dict_data['price_exact_ttc__min']
                if max_ttc_price > dict_data['price_exact_ttc__max']:
                    max_ttc_price = dict_data['price_exact_ttc__max']
                self.queryset = self.queryset.filter(
                    price_exact_ttc__range=(
                        min_ttc_price - 1e-2,
                        max_ttc_price + 1e-2
                    )
                )
        except ValueError:
            pass
        except TypeError:
            pass

        order = request.GET.get("order", None)

        if order is not None:
            order = order.lower()
            if order == "asc":
                self.ordering = "price_exact_ttc"
            elif order == "desc":
                self.ordering = "-price_exact_ttc"
            else:
                order = None

            dict_data.update({"order": order})
        else:
            dict_data.update({"order": order})

        if self.ordering is not None:
            self.queryset = self.queryset.order_by(self.ordering)

        dict_data["related_products"] = self.paginate_queryset(self.queryset)
        if dict_data["related_products"] is not None:
            serializer = self.get_serializer(dict_data)
            return self.get_paginated_response(serializer.data)

        dict_data["related_products"] = self.queryset
        serializer = self.get_serializer(dict_data["related_products"])
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        return self.list_catalogue(request, **kwargs)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    def partial_update(self, request, *args, **kwargs):
        self.serializer_class = catalogue_serializers.AddToBasketSerializer
        self.queryset = self.queryset.annotate(
            **price_annotation_format()
        )
        instance = self.get_object()
        signer = Signer()

        data_patch = request.data.copy()
        basket = get_basket(signer, data_patch[settings.BASKET_SESSION_KEY])

        data_patch[settings.BASKET_SESSION_KEY] = basket
        serializer = self.get_serializer({"product": instance}, data=data_patch, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            update_basket(basket, instance.slug, quantity=data_patch['quantity'])
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({"basket": signer.sign_object(basket), **get_basket_len(basket)})

    @action(detail=False,
            methods=['GET'],
            url_path=r'categories/(?P<slug_category>[-\w]+)')
    def list_category(self, request, *_, **kwargs):
        return self.list_catalogue(request, **kwargs)

    def get_basket_queryset(self, basket):
        return super().get_queryset().filter(
            slug__in=tuple(basket.keys())
        ).annotate(
            **price_annotation_format(basket)
        ).annotate(
            **post_price_annotation_format()
        )

    def basket_treatment(self, basket_sign, promo_code):
        self.serializer_class = catalogue_serializers.BasketSurfaceSerializer
        signer = Signer()
        basket = get_basket(signer, basket_sign)

        if not bool(basket):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        products_queryset = self.filter_queryset(self.get_basket_queryset(basket))
        products, product_to_exclude, _ = product_to_exclude_(products_queryset, basket)
        promo_db = get_promo(basket, promo_code)

        aggregate = products_queryset.exclude(
            slug__in=product_to_exclude
        ).aggregate(
            **total_price_from_all_product(promo=promo_db)
        )

        context = {
            "products": list(products),
            "promo": promo_db,
            "basket_sign": signer.sign_object(basket),
            "deduce_tva": Decimal(
                aggregate['price_exact_ht_with_quantity__sum']
            ) * settings.TVA_PERCENT * settings.BACK_TWO_PLACES,
            "deduce_tva_promo": Decimal(
                aggregate.get('price_exact_ht_with_quantity_promo__sum', Decimal(0))
            ) * settings.TVA_PERCENT * settings.BACK_TWO_PLACES,
            **aggregate
        }
        serializer = self.get_serializer(context)
        return Response(serializer.data)

    @action(detail=False,
            methods=['GET'],
            url_path=r'basket/surface/(?P<basket_sign>[-:\w]+)/(?P<promo_code>[\w]+)')
    def basket_surface(self, request, *_, **kwargs):
        return self.basket_treatment(kwargs.get('basket_sign', None), kwargs.get('promo_code', None))

    @action(detail=False,
            methods=['POST'],
            url_path=r'basket/surface')
    def basket_update(self, request, *_, **kwargs):
        self.serializer_class = catalogue_serializers.UpdateBasketSerializer
        signer = Signer()
        basket = get_basket(signer, request.data.get('basket_sign'))

        if not bool(basket):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        products_queryset = self.filter_queryset(self.get_basket_queryset(basket))
        products, product_to_exclude, basket_enum = product_to_exclude_(products_queryset, basket)

        list_instance = [{'product': product} for product in products]
        list_data = tuple({} for _ in range(len(products)))

        for key, value in request.data.items():
            regex = re.search(r'^[^_]+_([^_]+)_(.+)$', key)
            slug = regex.group(1)
            attr = regex.group(2)
            index = basket_enum[slug]
            list_data[index].update({attr: value})

        serializer = self.get_serializer(list_instance, data=list_data, partial=True, many=True)
        serializer.is_valid(raise_exception=True)

        try:
            for slug, i in basket_enum.items():
                update_basket(basket, slug, quantity=list_data[i]['quantity'], type_='set_quantity')
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if len(product_to_exclude) > 0:
            status_ = status.HTTP_205_RESET_CONTENT
        else:
            status_ = status.HTTP_200_OK

        return Response({"basket": signer.sign_object(basket), **get_basket_len(basket)}, status=status_)

    def retrieve(self, request, *args, **kwargs):
        self.queryset = self.queryset.annotate(
            **price_annotation_format()
        )
        return super().retrieve(request, *args, **kwargs)
