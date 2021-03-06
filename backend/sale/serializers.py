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
    address = AddressSerializer(source="order_address", many=True, default=None)
    ordered_is_enable = serializers.BooleanField()
    effective_end_time_payment = serializers.DateTimeField()
    ordered_is_ready_to_delete = serializers.BooleanField()

    def to_representation(self, instance):
        ret = super(OrderedSerializer, self).to_representation(instance)
        ret.update({
            'price_exact_ttc_with_quantity_sum':
                Decimal(instance.price_exact_ttc_with_quantity_sum) * settings.BACK_TWO_PLACES,
            'price_exact_ttc_with_quantity_sum_promo':
                Decimal(instance.price_exact_ttc_with_quantity_sum_promo) *
                settings.BACK_TWO_PLACES if instance.price_exact_ttc_with_quantity_sum_promo else None,
            'price_exact_ht_with_quantity_sum':
                Decimal(instance.price_exact_ht_with_quantity_sum) * settings.BACK_TWO_PLACES,
            'price_exact_ht_with_quantity_sum_promo':
                Decimal(instance.price_exact_ht_with_quantity_sum_promo) *
                settings.BACK_TWO_PLACES if instance.price_exact_ht_with_quantity_sum_promo else None,
        })

        for i, product in enumerate(ret["from_ordered"]):
            ret["from_ordered"][i]["price_exact_ttc_with_quantity"] = \
                Decimal(product["price_exact_ttc_with_quantity"]) * settings.BACK_TWO_PLACES
            ret["from_ordered"][i]["price_exact_ht_with_quantity"] = \
                Decimal(product["price_exact_ht_with_quantity"]) * settings.BACK_TWO_PLACES
            ret["from_ordered"][i]["price_exact_ht"] = \
                Decimal(product["price_exact_ht"]) * settings.BACK_TWO_PLACES
            ret["from_ordered"][i]["price_exact_ttc"] = \
                Decimal(product["price_exact_ttc"]) * settings.BACK_TWO_PLACES

        ret["deduce_tva"] = ret['price_exact_ht_with_quantity_sum'] * settings.TVA_PERCENT * settings.BACK_TWO_PLACES,

        if ret['price_exact_ht_with_quantity_sum_promo']:
            deduce_tva_promo = ret['price_exact_ht_with_quantity_sum_promo'] \
                               * settings.TVA_PERCENT * settings.BACK_TWO_PLACES
        else:
            deduce_tva_promo = Decimal(0)

        ret["deduce_tva_promo"] = deduce_tva_promo
        ret["DELIVERY_MODE_CHOICES"] = sale_models.DELIVERY_MODE_CHOICES
        ret["delivery_value"] = Decimal(ret["delivery_value"]) * settings.BACK_TWO_PLACES \
            if ret["delivery_value"] else None
        ret["AMOUNT_FINAL"] = Decimal(get_amount(instance, with_delivery=True)) * settings.BACK_TWO_PLACES

        amount = get_amount(instance, with_promo=False) * settings.BACK_TWO_PLACES
        ret["CAN_PAY"] = instance.email and instance.phone and (
                settings.DELIVERY_FREE_GT <= amount or instance.delivery_value is not None
        ) and len(instance.order_address.all())

        return ret

    def update(self, instance, validated_data):
        if instance.payment_status:
            return instance

        if validated_data.get('email', None) is not None:
            instance.email = validated_data['email']

        if validated_data.get('phone', None) is not None:
            instance.phone = validated_data['phone']

        if validated_data.get('delivery_mode', None) is not None:
            amount = get_amount(instance, with_promo=False) * settings.BACK_TWO_PLACES

            if settings.DELIVERY_FREE_GT > amount:
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
            if 1 <= len(validated_data['order_address']) <= 2 and bool(validated_data['order_address'][0]):
                address_ = list(instance.order_address.all())

                if len(validated_data['order_address']) == 1 and len(address_) == 2:
                    address_[1].delete()

                for i, address in enumerate(validated_data['order_address']):
                    try:
                        p = {'pk': address_[i].id}
                    except IndexError:
                        p = {'pk': None}

                    sale_models.Address.objects.update_or_create(defaults=address, **p)

        instance.save()
        return instance

    def validate_address(self, attrs):
        if 1 <= len(attrs) <= 2 and bool(attrs[0]):
            for address in attrs:
                address['order'] = self.instance.pk

            addressSerializer = AddressSerializer(data=attrs, many=True)
            addressSerializer.is_valid(raise_exception=True)

            for address in attrs:
                address['order'] = self.instance

        return attrs

    class Meta:
        model = sale_models.Ordered
        exclude = ('products',)
