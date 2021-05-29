from django import forms

from sale.models import Ordered

BOOKING_SESSION_KEY = "ordered_instance_pk"


class OrderedInformation(forms.ModelForm):
    class Meta:
        model = Ordered
        exclude = ('products',
                   'payment_status',
                   'price_exact_ttc_with_quantity_sum',
                   'price_exact_ht_with_quantity_sum',
                   'createdAt',
                   'endOfLife')


class OrderedForm(forms.Form):
    pass
