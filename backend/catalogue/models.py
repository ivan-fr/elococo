import os
import shutil
import time
from treebeard.mp_tree import MP_Node

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.text import slugify


def product_image_path(instance, filename: str):
    return 'product-{0}/{1}.{2}'.format(slugify(instance.product.name), time.time_ns(), filename.split('.')[-1])


class Category(MP_Node):
    category = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    node_order_by = ['category']

    def __str__(self):
        return '%s' % self.category

    def save(self, *args, **kwargs):
        self.slug = slugify(self.category)
        super(Category, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "categories"


class EnableProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(enable_sale=True)


class Product(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(primary_key=True)
    description = models.TextField()
    price = models.PositiveSmallIntegerField()
    TTC_price = models.BooleanField(default=False)

    reduction = models.PositiveSmallIntegerField(
        validators=(MaxValueValidator(100),), default=0)
    reduction_end = models.DateField(null=True, blank=True)
    stock = models.PositiveSmallIntegerField(default=0)

    date = models.DateField(auto_now_add=True)
    dateUpdate = models.DateField(auto_now=True)
    categories = models.ManyToManyField(Category, related_name="products")
    enable_comment = models.BooleanField(default=False)
    enable_sale = models.BooleanField(default=False)

    objects = models.Manager()
    enable_objects = EnableProductManager()

    def compute_basket_oder(self, basket_enum):
        return basket_enum[self.slug]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-date', '-dateUpdate')


@receiver(pre_delete, sender=Product)
def product_pre_delete(**kwargs):
    name = 'product-{0}'.format(slugify(kwargs.get('instance').name))
    path = settings.MEDIA_ROOT / name
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except Exception:
            pass


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=product_image_path)
    url_host = models.URLField(null=True, blank=True)


@receiver(pre_delete, sender=ProductImage)
def product_pre_delete(**kwargs):
    if kwargs.get('instance').url_host is not None:
        return

    image = kwargs.get('instance').image
    path = settings.MEDIA_ROOT / image.name
    if os.path.exists(path):
        os.remove(path)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    text = models.TextField(blank=False, null=False)
    date = models.DateField(auto_now_add=True)
