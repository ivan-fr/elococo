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
        widgets = {
            'first_name': forms.TextInput(attrs={"class": "form-control"}),
            'last_name': forms.TextInput(attrs={"class": "form-control"}),
            'email': forms.EmailInput(attrs={"class": "form-control"}),
            'address': forms.TextInput(attrs={"class": "form-control"}),
            'address2': forms.TextInput(attrs={"class": "form-control"}),
            'postal_code': forms.TextInput(attrs={"class": "form-control"}),
            'city': forms.TextInput(attrs={"class": "form-control"}),
            'phone': forms.TextInput(attrs={"class": "form-control"}),
        }


class OrderedForm(forms.Form):
    pass
