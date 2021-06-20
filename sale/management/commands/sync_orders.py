from django.core.management.base import BaseCommand
from django.db import transaction

from catalogue.models import Product
from sale.bdd_calculations import default_ordered_annotation_format
from sale.models import Ordered


class Command(BaseCommand):
    help = 'Update the database for clean orders'

    def handle(self, *args, **options):
        orders = Ordered.objects.annotate(
            **default_ordered_annotation_format()
        ).filter(
            ordered_is_ready_to_delete=True
        ).prefetch_related("from_ordered", "from_ordered__to_product",
                           "from_ordered__to_product__box",
                           "from_ordered__to_product__elements")

        count = orders.count()
        self.stdout.write(self.style.WARNING(
            f"There is {count} no valid to delete."
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
                        product.effective_stock += ordered_product.quantity
                        products.add(product)
            Product.objects.bulk_update(list(products), ("stock",))
            orders.delete()

        self.stdout.write(self.style.SUCCESS(
            f"There is {count} order(s) deleted."
        ))
