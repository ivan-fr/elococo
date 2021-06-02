import datetime
import uuid

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from catalogue.forms import BASKET_MAX_QUANTITY_PER_FORM
from catalogue.models import Product

TIME_ORDERED_LIFE_MINUTES = 45
TIME_ORDERED_CLOSE_PAYMENT_TIME_BEFORE_END = 15
ORDER_SECRET_LENGTH = 30

def phone_regex():
    return RegexValidator(regex="^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$",
                          message="Le numéro ne respecte pas le bon format.")


class Ordered(models.Model):
    order_number = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(null=True)
    first_name = models.CharField(_("prénom"), null=True, max_length=255)
    last_name = models.CharField(_("nom de famille"), null=True, max_length=255)
    address = models.CharField(_("ligne adresse 1"), max_length=255, null=True)
    address2 = models.CharField(_("ligne adresse 2"), max_length=255, null=True, blank=True)
    postal_code = models.PositiveIntegerField(_("code postal"), null=True)
    city = models.CharField(_("ville"), max_length=255, null=True)
    phone = models.CharField("téléphone", validators=(phone_regex(),), max_length=20)
    secrets = models.CharField(max_length=ORDER_SECRET_LENGTH)

    products = models.ManyToManyField(Product,
                                      through='sale.OrderedProduct',
                                      through_fields=('from_ordered',
                                                      'to_product'))
    payment_status = models.BooleanField(default=False)

    price_exact_ttc_with_quantity_sum = models.PositiveIntegerField()
    price_exact_ht_with_quantity_sum = models.PositiveIntegerField()

    createdAt = models.DateTimeField()
    endOfLife = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.createdAt = now()
        self.endOfLife = self.createdAt + datetime.timedelta(minutes=TIME_ORDERED_LIFE_MINUTES)
        super().save(*args, **kwargs)


class OrderedProduct(models.Model):
    from_ordered = models.ForeignKey(Ordered, on_delete=models.CASCADE,
                                     related_name='from_ordered')
    to_product = models.ForeignKey(Product, on_delete=models.SET_NULL,
                                   related_name="to_product", null=True)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),
                                                            MaxValueValidator(BASKET_MAX_QUANTITY_PER_FORM)])

    product_name = models.CharField(max_length=50)
    effective_reduction = models.PositiveSmallIntegerField(validators=(MaxValueValidator(100),), default=0)
    price_exact_ttc = models.PositiveIntegerField()
    price_exact_ht = models.PositiveIntegerField()
    price_exact_ttc_with_quantity = models.PositiveIntegerField()
    price_exact_ht_with_quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('from_ordered', 'to_product')
