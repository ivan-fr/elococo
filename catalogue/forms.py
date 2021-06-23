from django import forms
from django.conf import settings
from django.forms import BaseFormSet

from sale.bdd_calculations import get_promo


def factor_clean(product_instance, basket):
    if product_instance is None:
        raise forms.ValidationError("Le produit n'existe pas.")

    if not product_instance.enable_sale:
        raise forms.ValidationError("Le produit n'est pas disponible à la vente.")

    if len(basket) >= settings.MAX_BASKET_PRODUCT:
        raise forms.ValidationError(
            f"Nombre maximal ({settings.MAX_BASKET_PRODUCT}) de produits atteint dans le panier."
        )


class ProductFormSet(BaseFormSet):
    def __init__(self, products_queryset, session, *args, **kwargs):
        super(ProductFormSet, self).__init__(*args, **kwargs)
        self.products_queryset = products_queryset
        self.session = session

    def get_form_kwargs(self, form_index):
        form_kwargs = super(ProductFormSet, self).get_form_kwargs(form_index)
        if form_index is not None:
            try:
                form_kwargs[settings.PRODUCT_INSTANCE_KEY] = self.products_queryset[form_index]
            except IndexError:
                pass
        form_kwargs["session"] = self.session
        return form_kwargs


class AddToBasketForm(forms.Form):
    choices = tuple(range(1, settings.BASKET_MAX_QUANTITY_PER_FORM + 1))
    quantity = forms.ChoiceField(choices=((i, i) for i in choices),
                                 help_text="Choisir une quantité.",
                                 label="Quantité",
                                 widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        self.product_instance = kwargs.pop(settings.PRODUCT_INSTANCE_KEY, None)

        super(AddToBasketForm, self).__init__(*args, **kwargs)
        print(self.product_instance.quantity_from_basket_box)
        if self.product_instance is not None:
            self.choices = range(
                1,
                min(
                    self.product_instance.post_effective_stock_with_basket,
                    settings.BASKET_MAX_QUANTITY_PER_FORM
                ) + 1
            )
            self.fields["quantity"].choices = ((i, i) for i in self.choices)

    def clean_quantity(self):
        try:
            data = int(self.cleaned_data['quantity'])
            return data
        except ValueError:
            raise forms.ValidationError("Valeur incompatible.")

    def clean(self):
        basket = self.session.get(settings.BASKET_SESSION_KEY, {})
        factor_clean(self.product_instance, basket)

        if self.cleaned_data.get('quantity', None) is None:
            raise forms.ValidationError("Incohérence dans le formulaire.")

        if bool(basket) and basket.get(self.product_instance.slug, None) is not None:
            if self.cleaned_data["quantity"] + basket[self.product_instance.slug]["quantity"] > max(self.choices):
                raise forms.ValidationError(
                    f"""Votre panier possède déjà {basket[self.product_instance.slug]["quantity"]} quantité 
                    de ce produit, en ajoutant {self.cleaned_data["quantity"]} vous depassez la limite autorisé."""
                )

        return super(AddToBasketForm, self).clean()

    class Meta:
        labels = {"quantity": "quantité"}


class UpdateBasketForm(AddToBasketForm):
    remove = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
                                label="Supprimer")

    def clean(self):
        if self.cleaned_data.get("remove", False):
            return super(AddToBasketForm, self).clean()

        basket = self.session.get(settings.BASKET_SESSION_KEY, {})
        factor_clean(self.product_instance, basket)

        if self.cleaned_data.get('quantity', None) is None:
            self.add_error("quantity", forms.ValidationError("Incohérence dans le formulaire."))

        elif self.cleaned_data["quantity"] > max(self.choices):
            self.add_error("quantity", forms.ValidationError(
                f"""vous depassez la limite autorisé avec cette quantité ({self.cleaned_data['quantity']}) demandé."""
            ))

        return super(AddToBasketForm, self).clean()


class PromoForm(forms.Form):
    code_promo = forms.CharField(max_length=settings.PROMO_SECRET_LENGTH, min_length=4,
                                 widget=forms.TextInput(attrs={"class": "form-control"}), )

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        super(PromoForm, self).__init__(*args, **kwargs)

    def clean_code_promo(self):
        basket = self.session.get(settings.BASKET_SESSION_KEY, {})

        if not bool(basket):
            raise forms.ValidationError("Le panier est vide.")

        self.cleaned_data["code_promo"] = get_promo(basket, self.cleaned_data["code_promo"])
        if self.cleaned_data["code_promo"] is None:
            raise forms.ValidationError("Ce code n'existe pas ou soit ne respecte pas certaines conditions.")
        return self.cleaned_data["code_promo"]
