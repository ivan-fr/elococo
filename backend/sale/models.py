import datetime
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator
from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from catalogue.models import Product
from elococo.settings import BACK_TWO_PLACES

PROMO_CHOICES = [
    ("cu", 'Currency'),
    ("pe", 'Percentage'),
]


def phone_regex():
    return RegexValidator(regex=r"^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$",
                          message="Le numéro ne respecte pas le bon format.")


class Promo(models.Model):
    code = models.CharField("Code promo", max_length=settings.PROMO_SECRET_LENGTH, blank=True,
                            validators=[MinLengthValidator(4)], primary_key=True)
    type = models.CharField("Type", choices=PROMO_CHOICES, default="currency", max_length=2)
    value = models.PositiveSmallIntegerField("Valeur", validators=[MinValueValidator(1), MaxValueValidator(100)])

    max_time = models.PositiveSmallIntegerField(
        "Nombre d'utilisation max", null=True, blank=True,
        validators=[MinValueValidator(1), ]
    )

    startOfLife = models.DateTimeField("Début d'activation", null=True, blank=True)
    endOfLife = models.DateTimeField("Fin d'activation", null=True, blank=True)

    min_ht = models.PositiveSmallIntegerField("Min TTC", null=True, blank=True, validators=[MinValueValidator(1), ])
    min_products_basket = models.PositiveSmallIntegerField(
        "Min products basket",
        validators=[MinValueValidator(1),
                    MaxValueValidator(settings.MAX_BASKET_PRODUCT)],
        default=1
    )


DELIVERY_SPEED = "ds"
DELIVERY_ORDINARY = "do"

DELIVERY_MODE_CHOICES = (
    (DELIVERY_SPEED, f'Livraison rapide +{settings.DELIVERY_SPEED.quantize(BACK_TWO_PLACES)}€ (sous 24H)'),
    (DELIVERY_ORDINARY, f'Livraison standard +{settings.DELIVERY_ORDINARY.quantize(BACK_TWO_PLACES)}€ (sous 48H)'),
)


class Ordered(models.Model):
    order_number = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(null=True)
    phone = models.CharField("téléphone", validators=(phone_regex(),), max_length=20, null=True, blank=True)
    secrets = models.CharField(max_length=settings.ORDER_SECRET_LENGTH)

    products = models.ManyToManyField(
        Product,
        through='sale.OrderedProduct',
        through_fields=('from_ordered',
                        'to_product')
    )
    payment_status = models.BooleanField(default=False)
    invoice_date = models.DateTimeField(null=True)

    price_exact_ttc_with_quantity_sum = models.PositiveIntegerField()
    price_exact_ht_with_quantity_sum = models.PositiveIntegerField()

    createdAt = models.DateTimeField()
    endOfLife = models.DateTimeField()

    delivery_mode = models.CharField(
        "Mode de livraison",
        max_length=2,
        choices=DELIVERY_MODE_CHOICES,
        default=DELIVERY_SPEED,
        null=True
    )
    delivery_value = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        null=True
    )

    promo = models.ForeignKey(Promo, on_delete=models.SET_NULL, null=True)
    promo_value = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], null=True)
    promo_type = models.CharField(choices=PROMO_CHOICES, max_length=2, null=True)
    price_exact_ttc_with_quantity_sum_promo = models.PositiveIntegerField(null=True)
    price_exact_ht_with_quantity_sum_promo = models.PositiveIntegerField(null=True)

    def save(self, *args, **kwargs):
        if self.createdAt is None:
            self.createdAt = now()
            self.endOfLife = self.createdAt + datetime.timedelta(minutes=settings.TIME_ORDERED_LIFE_MINUTES)
        super().save(*args, **kwargs)


class Address(models.Model):
    order = models.ForeignKey(Ordered, on_delete=models.CASCADE, related_name="order_address")
    first_name = models.CharField(_("prénom"), max_length=255)
    last_name = models.CharField(_("nom de famille"), max_length=255)
    address = models.CharField(_("ligne adresse 1"), max_length=255)
    address2 = models.CharField(_("ligne adresse 2"), max_length=255, null=True, blank=True)
    postal_code = models.PositiveIntegerField(_("code postal"))
    city = models.CharField(_("ville"), max_length=255)


class OrderedProduct(models.Model):
    from_ordered = models.ForeignKey(Ordered,
                                     on_delete=models.CASCADE,
                                     related_name='from_ordered')
    to_product = models.ForeignKey(Product,
                                   on_delete=models.SET_NULL,
                                   related_name="to_product",
                                   null=True)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),
                                                            MaxValueValidator(settings.BASKET_MAX_QUANTITY_PER_FORM)])

    product_name = models.CharField(max_length=50)
    effective_reduction = models.PositiveSmallIntegerField(
        validators=(MaxValueValidator(100),),
        default=0
    )
    price_exact_ttc = models.PositiveIntegerField()
    price_exact_ht = models.PositiveIntegerField()
    price_exact_ttc_with_quantity = models.PositiveIntegerField()
    price_exact_ht_with_quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('from_ordered', 'to_product')
