import re
import secrets
import string
from decimal import Decimal

from django.conf import settings
from django.core.signing import Signer
from django.db import IntegrityError
from django.db import transaction
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response

import catalogue.models as catalogue_models
import sale.models as sale_models
from catalogue.bdd_calculations import price_annotation_format, post_price_annotation_format, \
    total_price_from_all_product
from catalogue.rest_views import get_basket, product_to_exclude_, get_basket_dict
from sale.bdd_calculations import get_promo, default_ordered_annotation_format
from sale.serializers import OrderedSerializer, PromoSerializer


class SaleBasketViewSet(viewsets.GenericViewSet):
    queryset = catalogue_models.Product.enable_objects.filter(
        stock__gt=0
    )
    serializer_class = None

    def get_basket_queryset(self, basket):
        return self.get_queryset().filter(
            slug__in=tuple(basket.keys())
        ).annotate(
            **price_annotation_format(basket)
        ).annotate(
            **post_price_annotation_format()
        )

    def create(self, request, *args, **kwargs):
        basket = request.data.get('basket', None)
        promo = request.data.get('promo', None)

        signer = Signer()
        basket = get_basket(signer, basket)

        if not bool(basket):
            return Response(status=status.HTTP_403_FORBIDDEN)

        products_queryset = self.filter_queryset(self.get_basket_queryset(basket))
        products, _, _, basket_update = product_to_exclude_(products_queryset, basket)
        promo_db = get_promo(basket, promo)

        if basket_update:
            return Response(get_basket_dict(signer, basket, PromoSerializer(promo_db).data),
                            status=status.HTTP_401_UNAUTHORIZED)

        aggregate = products_queryset.aggregate(
            **total_price_from_all_product(promo=promo_db)
        )

        try:
            with transaction.atomic():
                dict_ = {}
                if promo is not None:
                    dict_.update({
                        "promo": promo, "promo_value": promo.value, "promo_type": promo.type,
                        "price_exact_ttc_with_quantity_sum_promo": int(
                            aggregate["price_exact_ttc_with_quantity_promo__sum"] *
                            Decimal(100.)
                        ),
                        "price_exact_ht_with_quantity_sum_promo": int(
                            aggregate["price_exact_ht_with_quantity_promo__sum"] *
                            Decimal(100.)
                        ),
                    })

                ordered = sale_models.Ordered.objects.create(
                    price_exact_ht_with_quantity_sum=int(
                        aggregate["price_exact_ht_with_quantity__sum"].quantize(settings.BACK_TWO_PLACES) *
                        Decimal(100.)
                    ),
                    price_exact_ttc_with_quantity_sum=int(
                        aggregate["price_exact_ttc_with_quantity__sum"].quantize(settings.BACK_TWO_PLACES) *
                        Decimal(100.)
                    ),
                    secrets=''.join(secrets.choice(string.ascii_lowercase)
                                    for _ in range(settings.ORDER_SECRET_LENGTH)),
                    **dict_
                )

                ordered_product = []
                for product in products:
                    if product.effective_basket_quantity != basket[product.slug]:
                        raise ValueError()

                    ordered_product.append(
                        sale_models.OrderedProduct(
                            from_ordered=ordered,
                            to_product=product,
                            product_name=product.name,
                            effective_reduction=product.effective_reduction,
                            price_exact_ht=int(
                                product.price_exact_ht.quantize(
                                    settings.BACK_TWO_PLACES) * Decimal(100.)
                            ),
                            price_exact_ttc=int(
                                product.price_exact_ttc.quantize(
                                    settings.BACK_TWO_PLACES) * Decimal(100.)
                            ),
                            price_exact_ht_with_quantity=int(
                                product.price_exact_ht_with_quantity.quantize(settings.BACK_TWO_PLACES) *
                                Decimal(100.)
                            ),
                            price_exact_ttc_with_quantity=int(
                                product.price_exact_ttc_with_quantity.quantize(settings.BACK_TWO_PLACES) *
                                Decimal(100.)
                            ),
                            quantity=product.effective_basket_quantity
                        )
                    )

            sale_models.OrderedProduct.objects.bulk_create(ordered_product)
        except ValueError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except IntegrityError():
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response({'order': ordered.pk}, status=status.HTTP_201_CREATED)


class SaleOrderViewSet(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = sale_models.Ordered.objects.annotate(
        **default_ordered_annotation_format()
    ).prefetch_related(
        "order_address", "from_ordered", "from_ordered__to_product",
        "from_ordered__to_product__productimage_set"
    )
    serializer_class = OrderedSerializer

    def partial_update(self, request, *args, **kwargs):
        data = request.data.copy()
        address = [{}, {}]

        for key, value in data.items():
            regex = re.search(r'^[^_]+_([^_]+)_(.+)$', key)

            if regex is None:
                continue

            index = regex.group(1)
            attr = regex.group(2)
            address[int(index)].update({attr: value})
            data.pop(key)

        data["order_address"] = address
        request.data = data

        return super(SaleOrderViewSet, self).partial_update(request, *args, **kwargs)
