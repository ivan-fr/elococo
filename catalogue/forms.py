from django import forms
from django.forms import BaseFormSet

BASKET_SESSION_KEY = "basket"
MAX_BASKET_PRODUCT = 5
PRODUCT_INSTANCE_KEY = "product_instance"


class ProductFormSet(BaseFormSet):
    def __init__(self, products_queryset, *args, **kwargs):
        super(ProductFormSet, self).__init__(*args, **kwargs)
        self.products_queryset = products_queryset

    def get_form_kwargs(self, form_index):
        form_kwargs = super(ProductFormSet, self).get_form_kwargs(form_index)
        if form_index is not None:
            try:
                form_kwargs[PRODUCT_INSTANCE_KEY] = self.products_queryset[form_index]
            except IndexError:
                pass
        return form_kwargs


def clean_treatment(self, super_call):
    if self.product_instance is None:
        raise forms.ValidationError("Le produit n'existe pas.")

    if self.session is None:
        basket = {}
    else:
        basket = self.session.get(BASKET_SESSION_KEY, {})

    if len(basket) > MAX_BASKET_PRODUCT:
        raise forms.ValidationError(
            f"Nombre maximal ({MAX_BASKET_PRODUCT}) de produits atteint dans le panier"
        )

    if self.cleaned_data.get('quantity', None) is None:
        raise forms.ValidationError("Incohérence dans le formulaire.")

    if self.cleaned_data["quantity"] > self.product_instance.stock:
        raise forms.ValidationError(
            f"""Vous avez depassé le stock disponible de ce
             produit avec cette quantité ({self.cleaned_data['quantity']}) demandé."""
        )

    if bool(basket) and basket.get(self.product_instance.slug, None) is not None:
        if self.cleaned_data["quantity"] + basket[self.product_instance.slug]["quantity"] > max(self.choices):
            raise forms.ValidationError(
                f"Vous ne pouvez pas mettre plus de {max(self.choices)} de ce produit dans votre panier."
            )

        if self.cleaned_data["quantity"] + basket[self.product_instance.slug]["quantity"] > self.product_instance.stock:
            raise forms.ValidationError(
                f"""Vous avez depassé le stock disponible de ce produit
                 en essayant d'ajouter cette quantité ({self.cleaned_data["quantity"]}) dans votre panier."""
            )

    return super_call(super_call, self).clean()


class AddToBasketForm(forms.Form):
    choices = tuple(range(1, 10))
    quantity = forms.ChoiceField(choices=((i, i) for i in choices),
                                 help_text="Choisir une quantité.",
                                 label="Quantiter",
                                 widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        self.product_instance = kwargs.pop(PRODUCT_INSTANCE_KEY, None)
        super(AddToBasketForm, self).__init__(*args, **kwargs)

    def clean_quantity(self):
        try:
            data = int(self.cleaned_data['quantity'])
            return data
        except ValueError:
            raise forms.ValidationError("Valeur incompatible")

    def clean(self):
        return clean_treatment(self, AddToBasketForm)


class UpdateBasketForm(AddToBasketForm):
    remove = forms.BooleanField(required=False)

    def clean(self):
        if self.cleaned_data.get("remove", False):
            return super(AddToBasketForm, self).clean()
        return super(UpdateBasketForm, self).clean()
