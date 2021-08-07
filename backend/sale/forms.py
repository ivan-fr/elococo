from sale import get_amount
import secrets
import string
from decimal import Decimal

from django import forms
from django.conf import settings

from elococo.settings import BACK_TWO_PLACES
from sale.models import Address, Ordered, Promo, DELIVERY_SPEED


class AddressFormSet(forms.BaseModelFormSet):
    def __init__(self, queryset, ordered_queryset, *args, **kwargs):
        super(AddressFormSet, self).__init__(queryset=queryset, *args, **kwargs)
        self.ordered = ordered_queryset

    def get_form_kwargs(self, form_index):
        form_kwargs = super(AddressFormSet, self).get_form_kwargs(form_index)
        form_kwargs[settings.ORDERED_INSTANCE_KEY] = self.ordered
        return form_kwargs


class CheckoutForm(forms.Form):
    pass


class RetrieveOrderForm(forms.Form):
    pk = forms.UUIDField(widget=forms.TextInput(
        attrs={"class": "form-control"}))
    secrets = forms.CharField(
        max_length=settings.ORDER_SECRET_LENGTH,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    attempt = forms.BooleanField()


class DeliveryMode(forms.ModelForm):
    class Meta:
        model = Ordered
        exclude = (
            'products',
            'payment_status',
            'price_exact_ttc_with_quantity_sum',
            'price_exact_ht_with_quantity_sum',
            'createdAt',
            'phone',
            'email',
            'endOfLife', 'secrets', 'invoice_date', "promo", "promo_value", "promo_type",
            'price_exact_ttc_with_quantity_sum_promo', 'price_exact_ht_with_quantity_sum_promo',
            'delivery_value'
        )

    def save(self, commit=True):
        order = super().save(commit=False)

        amount = get_amount(order, with_promo=False) * BACK_TWO_PLACES
        amount = amount.quantize(BACK_TWO_PLACES)

        if settings.DELIVERY_FREE_GT <= amount:
            return order

        if order.delivery_mode == DELIVERY_SPEED:
            order.delivery_value = int(settings.DELIVERY_SPEED.quantize(BACK_TWO_PLACES) * Decimal(100.))
        else:
            order.delivery_value = int(settings.DELIVERY_ORDINARY.quantize(BACK_TWO_PLACES) * Decimal(100.))

        order.save()
        return order


class OrderedInformation(forms.ModelForm):
    class Meta:
        model = Ordered
        exclude = (
            'products',
            'payment_status',
            'price_exact_ttc_with_quantity_sum',
            'price_exact_ht_with_quantity_sum',
            'createdAt',
            'delivery_mode',
            'endOfLife', 'secrets', 'invoice_date', "promo", "promo_value", "promo_type",
            'price_exact_ttc_with_quantity_sum_promo', 'price_exact_ht_with_quantity_sum_promo',
            'delivery_value'
        )


class AddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        self.order = kwargs.pop(settings.ORDERED_INSTANCE_KEY, None)

        super(AddressForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.order is None:
            raise forms.ValidationError("La commande n'existe pas.")
        return super().clean()

    def save(self, commit=True):
        address = super().save(commit=False)
        address.order = self.order
        address.save()

        return address

    class Meta:
        model = Address
        exclude = ("id",)


class OrderedForm(forms.Form):
    pass


class PromoForm(forms.ModelForm):
    def clean_code(self):
        if not self.cleaned_data["code"]:
            self.cleaned_data["code"] = ''.join(
                secrets.choice(string.ascii_lowercase + string.ascii_uppercase)
                for i in range(settings.PROMO_SECRET_LENGTH)
            )
        return self.cleaned_data["code"]

    class Meta:
        model = Promo
        fields = '__all__'
