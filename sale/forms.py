from django import forms

from sale.models import Address, Ordered, ORDER_SECRET_LENGTH

BOOKING_SESSION_KEY = "ordered_instance_pk"
BOOKING_SESSION_FILL_KEY = "ordered_is_filled"
BOOKING_SESSION_FILL_2_KEY = "ordered_is_filled_next"
ORDERED_INSTANCE_KEY = "ordered_instance_key"


class AddressFormSet(forms.BaseModelFormSet):
    def __init__(self, queryset, ordered_queryset, *args, **kwargs):
        super(AddressFormSet, self).__init__(queryset=queryset, *args, **kwargs)
        self.ordered = ordered_queryset

    def get_form_kwargs(self, form_index):
        form_kwargs = super(AddressFormSet, self).get_form_kwargs(form_index)
        form_kwargs[ORDERED_INSTANCE_KEY] = self.ordered
        return form_kwargs


class CheckoutForm(forms.Form):
    pass


class RetrieveOrderForm(forms.Form):
    pk = forms.UUIDField(widget=forms.TextInput(
        attrs={"class": "form-control"}))
    secrets = forms.CharField(
        max_length=ORDER_SECRET_LENGTH,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )


WIDGETS_FILL_NEXT = {
    'first_name': forms.TextInput(attrs={"class": "form-control"}),
    'last_name': forms.TextInput(attrs={"class": "form-control"}),
    'address': forms.TextInput(attrs={"class": "form-control"}),
    'address2': forms.TextInput(attrs={"class": "form-control"}),
    'postal_code': forms.TextInput(attrs={"class": "form-control"}),
    'city': forms.TextInput(attrs={"class": "form-control"}),
}


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

class AddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        self.order = kwargs.pop(ORDERED_INSTANCE_KEY, None)

        super(AddressForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.order is None:
            raise forms.ValidationError("La commande n'existe pas.")
        return super().clean()

    def save(self, commit: bool):
        address = super().save(commit=False)
        address.order = self.order
        address.save()

    class Meta:
        model = Address
        exclude = ("id",)


class OrderedForm(forms.Form):
    pass
