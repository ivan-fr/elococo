from django import forms
from catalogue.models import Product


class AddToBasketForm(forms.Form):
    quantity = forms.ChoiceField(choices=((i, i) for i in tuple(range(1, 10))),
                                 help_text="Choisir une quantité.",
                                 label="Quantiter",
                                 widget=forms.Select(attrs={"class": "form-select"}))
    product_slug = forms.SlugField(disabled=True)

    def clean_quantity(self):
        try:
            data = int(self.cleaned_data['quantity'])

        except ValueError:
            raise forms.ValidationError("Valeur incompatible")

        return data

    def clean(self):
        queryset = Product.objects.filter(slug__exact=self.cleaned_data['product_slug'])

        try:
            product = queryset.get()
            if self.cleaned_data.get('quantity', None) is None:
                raise forms.ValidationError("Incohérence dans le formulaire.")

            if self.cleaned_data.get('quantity', None) > product.stock:
                raise forms.ValidationError("Vous avez depassé le stock disponible avec cette demande.")
        except queryset.model.DoesNotExist:
            raise forms.ValidationError("Le produit n'existe pas.")

        return super(AddToBasketForm, self).clean()
