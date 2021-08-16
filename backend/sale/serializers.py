from decimal import Decimal

from django.conf import settings
from rest_framework import serializers

import sale.models as sale_models
from sale import get_amount


class PromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = sale_models.Promo
        fields = '__all__'


class OrderedProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = sale_models.OrderedProduct
        exclude = ('from_ordered',)


class ProductOrderedSerializer(serializers.ModelSerializer):
    class Meta:
        model = sale_models.OrderedProduct
        exclude = ('to_product',)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = sale_models.Address
        fields = '__all__'


class OrderedSerializer(serializers.ModelSerializer):
    from_ordered = OrderedProductSerializer(many=True)
    promo = PromoSerializer(default=None)
    order_address = AddressSerializer(many=True, default=None)

    def update(self, instance, validated_data):
        if instance.payment_status:
            return instance

        if validated_data.get('email', None) is not None:
            instance.email = validated_data['email']

        if validated_data.get('phone', None) is not None:
            instance.phone = validated_data['phone']

        if validated_data.get('delivery_mode', None) is not None:
            amount = get_amount(instance, with_promo=False) * settings.BACK_TWO_PLACES
            amount = amount.quantize(settings.BACK_TWO_PLACES)

            if settings.DELIVERY_FREE_GT <= amount:
                instance.delivery_mode = validated_data['delivery_mode']

                if instance.delivery_mode == sale_models.DELIVERY_SPEED:
                    instance.delivery_value = int(
                        settings.DELIVERY_SPEED.quantize(settings.BACK_TWO_PLACES) * Decimal(100.)
                    )
                else:
                    instance.delivery_value = int(
                        settings.DELIVERY_ORDINARY.quantize(settings.BACK_TWO_PLACES) * Decimal(100.)
                    )

        if validated_data.get('order_address', None) is not None:
            if len(validated_data['order_address']) <= 2:
                order_address = list(instance.order_address.all())

                for i, address in enumerate(validated_data['order_address']):
                    try:
                        p = {'pk': order_address[i].id}
                    except KeyError:
                        p = {}

                    sale_models.Address.objects.update_or_create(defaults=address, **p)

        instance.save()
        return instance

    class Meta:
        model = sale_models.Ordered
        exclude = ('products',)
