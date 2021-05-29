import datetime

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from catalogue.forms import BASKET_MAX_QUANTITY_PER_FORM
from catalogue.models import Product


class Ordered(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    meetings = models.ManyToManyField(Product,
                                      through='sale.models.OrderedProduct',
                                      through_fields=('from_ordered',
                                                      'to_meeting'))
    payment_status = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    too_late_accepted_payment = models.BooleanField(default=False)


class OrderedProduct(models.Model):
    from_ordered = models.ForeignKey(Ordered, on_delete=models.CASCADE,
                                     related_name='from_ordered')
    to_product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name="to_product")
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),
                                                            MaxValueValidator(BASKET_MAX_QUANTITY_PER_FORM)])

    createdAt = models.DateTimeField(auto_now_add=True)
    endOfLife = models.DateTimeField(auto_now_add=True)

    qrcode = models.ImageField(upload_to='qrcode/%Y/%m/%d/', null=True,
                               blank=True)

    def save(self, *args, **kwargs):
        self.endOfLife = self.createdAt + datetime.timedelta(minutes=45)
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('from_ordered', 'to_product')
