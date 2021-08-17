import re
import secrets
import string
from decimal import Decimal

import stripe
from django.conf import settings
from django.core.signing import Signer
from django.db import IntegrityError
from django.db import transaction
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

import catalogue.models as catalogue_models
import sale.models as sale_models
from catalogue.bdd_calculations import price_annotation_format, post_price_annotation_format, \
    total_price_from_all_product
from catalogue.rest_views import get_basket, product_to_exclude_, get_basket_dict
from sale import get_amount
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


class SaleOrderViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = sale_models.Ordered.objects.annotate(
        **default_ordered_annotation_format()
    ).prefetch_related(
        "order_address", "from_ordered", "from_ordered__to_product",
        "from_ordered__to_product__productimage_set"
    )
    serializer_class = OrderedSerializer

    @action(detail=True,
            methods=['POST'],
            url_path=r'payment')
    def payment(self, request, *args, **kwargs):
        instance = self.get_object()

        images = []

        for ordered_product in instance.from_ordered.all():
            product = ordered_product.to_product

            try:
                image_url = product.productimage_set.all()[0].image.url
                images.append(self.request.build_absolute_uri(image_url))
            except IndexError:
                continue

        images = images[:8]

        try:
            if instance.payment_status or not instance.ordered_is_enable:
                raise Exception()

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'eur',
                            'unit_amount_decimal': get_amount(instance, with_delivery=True).quantize(
                                settings.BACK_TWO_PLACES),
                            'product_data': {
                                'name': f'Order #{instance.pk}',
                                'images': images
                            },
                        },
                        'quantity': 1,
                    },
                ],
                payment_intent_data={
                    "capture_method": "manual",
                    "metadata": {
                        "pk_order": instance.pk
                    }
                },
                metadata={
                    "pk_order": instance.pk
                },
                customer_email=instance.email,
                mode='payment',
                success_url=f"{settings.URL_CHECKOUT}?success=true",
                cancel_url=f"{settings.URL_CHECKOUT}?cancel=true",
            )

            return Response({"checkout_url": checkout_session.url})
        except Exception as e:
            return Response({"checkout_url": None})

    def partial_update(self, request, *args, **kwargs):
        data = request.data.copy()
        address = [{}, {}]

        for key, value in request.data.items():
            regex = re.search(r'^[^_]+_([^_]+)_(.+)$', key)

            if regex is None:
                continue

            index = regex.group(1)
            attr = regex.group(2)
            address[int(index)].update({attr: value})
            del data[key]

        if not bool(address[1]):
            address = address[:1]

        data["address"] = address

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
