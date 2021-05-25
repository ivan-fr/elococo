from django import forms
from catalogue.models import Product


class AddToBasketForm(forms.Form):
    quantity = forms.ChoiceField(choices=((i, i) for i in tuple(range(1, 10))),
                                 help_text="Choisir une quantité.",
                                 label="Quantiter")
    product_slug = forms.SlugField(disabled=True)

    def clean(self):
        queryset = Product.objects.filter(slug__exact=self.changed_data['product_slug'])

        try:
            product = queryset.get()
            if self.changed_data['quantity'] > product.stock:
                raise forms.ValidationError("Vous avez depassé le stock disponible avec cette demande.")
        except queryset.model.DoesNotExist:
            raise forms.ValidationError("Le produit n'existe pas.")

        return super(AddToBasketForm, self).clean()
