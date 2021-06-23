from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

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
            orders.delete()

        self.stdout.write(self.style.SUCCESS(
            f"There is {count} order(s) deleted."
        ))
