from django import forms
from catalogue.models import Product

BASKET_SESSION_KEY = "basket"


class AddToBasketForm(forms.Form):
    choices = tuple(range(1, 10))
    quantity = forms.ChoiceField(choices=((i, i) for i in choices),
                                 help_text="Choisir une quantité.",
                                 label="Quantiter",
                                 widget=forms.Select(attrs={"class": "form-select"}))
    product_slug = forms.SlugField(disabled=True)

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        super(AddToBasketForm, self).__init__(*args, **kwargs)

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

            if self.cleaned_data["quantity"] > product.stock:
                raise forms.ValidationError(
                    f"""Vous avez depassé le stock disponible de ce
                     produit avec cette quantité ({self.cleaned_data['quantity']}) demandé."""
                )

            if self.session is None:
                basket = {}
            else:
                basket = self.session.get(BASKET_SESSION_KEY, {})

            if basket != {} and basket.get(product.slug, None) is not None:
                if self.cleaned_data["quantity"] + basket[product.slug]["quantity"] > max(self.choices):
                    raise forms.ValidationError(
                        f"Vous ne pouvez pas mettre plus de {max(self.choices)} de ce produit dans votre panier."
                    )

                if self.cleaned_data["quantity"] + basket[product.slug]["quantity"] > product.stock:
                    raise forms.ValidationError(
                        f"""Vous avez depassé le stock disponible de ce produit
                         en essayant d'ajouter cette quantité ({self.cleaned_data["quantity"]}) dans votre panier."""
                    )

        except queryset.model.DoesNotExist:
            raise forms.ValidationError("Le produit n'existe pas.")

        return super(AddToBasketForm, self).clean()
