from django import forms
from django.forms import BaseFormSet

BASKET_SESSION_KEY = "basket"
BASKET_MAX_QUANTITY_PER_FORM = 3
MAX_BASKET_PRODUCT = 8
PRODUCT_INSTANCE_KEY = "product_instance"


class ProductFormSet(BaseFormSet):
    def __init__(self, products_queryset, session, *args, **kwargs):
        super(ProductFormSet, self).__init__(*args, **kwargs)
        self.products_queryset = products_queryset
        self.session = session

    def get_form_kwargs(self, form_index):
        form_kwargs = super(ProductFormSet, self).get_form_kwargs(form_index)
        if form_index is not None:
            try:
                form_kwargs[PRODUCT_INSTANCE_KEY] = self.products_queryset[form_index]
            except IndexError:
                pass
        form_kwargs["session"] = self.session
        return form_kwargs


class AddToBasketForm(forms.Form):
    choices = tuple(range(1, BASKET_MAX_QUANTITY_PER_FORM + 1))
    quantity = forms.ChoiceField(choices=((i, i) for i in choices),
                                 help_text="Choisir une quantité.",
                                 label="Quantiter",
                                 widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        self.product_instance = kwargs.pop(PRODUCT_INSTANCE_KEY, None)

        super(AddToBasketForm, self).__init__(*args, **kwargs)

        if self.product_instance is not None:
            self.choices = range(1, min(self.product_instance.stock, BASKET_MAX_QUANTITY_PER_FORM) + 1)
            self.fields["quantity"].choices = ((i, i) for i in self.choices)

    def clean_quantity(self):
        try:
            data = int(self.cleaned_data['quantity'])
            return data
        except ValueError:
            raise forms.ValidationError("Valeur incompatible.")

    def clean(self):
        if self.product_instance is None:
            raise forms.ValidationError("Le produit n'existe pas.")

        basket = self.session.get(BASKET_SESSION_KEY, {})

        if len(basket) >= MAX_BASKET_PRODUCT:
            raise forms.ValidationError(
                f"Nombre maximal ({MAX_BASKET_PRODUCT}) de produits atteint dans le panier."
            )

        if self.cleaned_data.get('quantity', None) is None:
            raise forms.ValidationError("Incohérence dans le formulaire.")

        if self.cleaned_data["quantity"] > max(self.choices):
            raise forms.ValidationError(
                f"""vous depassez la limite autorisé avec cette quantité ({self.cleaned_data['quantity']}) demandé."""
            )

        if bool(basket) and basket.get(self.product_instance.slug, None) is not None:
            if self.cleaned_data["quantity"] + basket[self.product_instance.slug]["quantity"] > max(self.choices):
                raise forms.ValidationError(
                    f"""Votre panier possède déjà {basket[self.product_instance.slug]["quantity"]} quantité 
                    de ce produit, en ajoutant {self.cleaned_data["quantity"]} vous depassez la limite autorisé."""
                )

        return super(AddToBasketForm, self).clean()


class UpdateBasketForm(AddToBasketForm):
    remove = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    def clean(self):
        if self.cleaned_data.get("remove", False):
            return super(AddToBasketForm, self).clean()

        if self.product_instance is None:
            raise forms.ValidationError("Le produit n'existe pas.")

        basket = self.session.get(BASKET_SESSION_KEY, {})

        if len(basket) >= MAX_BASKET_PRODUCT:
            raise forms.ValidationError(
                f"Nombre maximal ({MAX_BASKET_PRODUCT}) de produits atteint dans le panier."
            )

        if self.cleaned_data.get('quantity', None) is None:
            self.add_error("quantity", forms.ValidationError("Incohérence dans le formulaire."))

        elif self.cleaned_data["quantity"] > max(self.choices):
            self.add_error("quantity", forms.ValidationError(
                f"""vous depassez la limite autorisé avec cette quantité ({self.cleaned_data['quantity']}) demandé."""
            ))

        return super(AddToBasketForm, self).clean()
