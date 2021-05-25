from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.validators import MaxValueValidator
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings
import time
import os
import shutil


def product_image_path(instance, filename: str):
    return 'product-{0}/{1}.{2}'.format(slugify(instance.product.name), time.time_ns(), filename.split('.')[-1])


class Category(models.Model):
    category = models.CharField(max_length=60)
    slug = models.SlugField(primary_key=True)

    class Meta:
        ordering = ('category',)


class Product(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(primary_key=True)
    description = models.TextField()
    price = models.PositiveSmallIntegerField()
    reduction = models.PositiveSmallIntegerField(validators=(MaxValueValidator(100),), default=0)
    reduction_end = models.DateField(null=True, blank=True)

    stock = models.PositiveSmallIntegerField(default=0)

    date = models.DateField(auto_now_add=True)
    dateUpdate = models.DateField(auto_now=True)
    categories = models.ManyToManyField(Category)
    enable_comment = models.BooleanField(default=False)
    enable_sale = models.BooleanField(default=False)

    class Meta:
        ordering = ('-date', '-dateUpdate')


@receiver(pre_delete, sender=Product)
def product_pre_delete(**kwargs):
    name = 'product-{0}'.format(slugify(kwargs.get('instance').name))
    path = settings.MEDIA_ROOT / name
    if os.path.exists(path):
        shutil.rmtree(path)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=product_image_path)


@receiver(pre_delete, sender=ProductImage)
def product_pre_delete(**kwargs):
    image = kwargs.get('instance').image
    path = settings.MEDIA_ROOT / image.name
    if os.path.exists(path):
        os.remove(path)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    text = models.TextField(blank=False, null=False)
    date = models.DateField(auto_now_add=True)
