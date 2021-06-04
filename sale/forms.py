from django import forms

from sale.models import Ordered, ORDER_SECRET_LENGTH

BOOKING_SESSION_KEY = "ordered_instance_pk"
BOOKING_SESSION_FILL_KEY = "ordered_is_filled"
BOOKING_SESSION_FILL_2_KEY = "ordered_is_filled_next"


class CheckoutForm(forms.Form):
    payment_method_nonce = forms.CharField(
        max_length=1000,
        widget=forms.widgets.HiddenInput,
    )


class RetrieveOrderForm(forms.Form):
    pk = forms.UUIDField(widget=forms.TextInput(attrs={"class": "form-control"}))
    secrets = forms.CharField(
        max_length=ORDER_SECRET_LENGTH,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )


"""
            'first_name': forms.TextInput(attrs={"class": "form-control"}),
            'last_name': forms.TextInput(attrs={"class": "form-control"}),
            'address': forms.TextInput(attrs={"class": "form-control"}),
            'address2': forms.TextInput(attrs={"class": "form-control"}),
            'postal_code': forms.TextInput(attrs={"class": "form-control"}),
            'city': forms.TextInput(attrs={"class": "form-control"}),
"""


class OrderedInformation(forms.ModelForm):
    class Meta:
        model = Ordered
        exclude = ('products',
                   'payment_status',
                   'price_exact_ttc_with_quantity_sum',
                   'price_exact_ht_with_quantity_sum',
                   'createdAt',
                   'endOfLife', 'secrets', 'invoice_date')
        widgets = {
            'phone': forms.TextInput(attrs={"class": "form-control"}),
            'email': forms.EmailInput(attrs={"class": "form-control"}),
        }


class OrderedForm(forms.Form):
    pass
