from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from catalogue.models import Product
from sale.models import Ordered


class Command(BaseCommand):
    help = 'clean orders'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            return

        orders = Ordered.objects.prefetch_related("from_ordered", "from_ordered__to_product",
                                                  "from_ordered__to_product__box",
                                                  "from_ordered__to_product__elements").all()

        count = orders.count()
        self.stdout.write(self.style.WARNING(
            f"There is {count} to delete."
        ))

        with transaction.atomic():
            products = set()
            for order in orders:
                for ordered_product in order.from_ordered.all():
                    product = ordered_product.to_product
                    if product.box is not None:
                        for box in product.box.all():
                            box.elements.stock += box.quantity * ordered_product.quantity
                            products.add(box.elements)
                    else:
                        product.stock += ordered_product.quantity
                        products.add(product)
            Product.objects.bulk_update(list(products), ("stock",))
            orders.delete()

        self.stdout.write(self.style.SUCCESS(
            f"There is {count} order(s) deleted."
        ))
