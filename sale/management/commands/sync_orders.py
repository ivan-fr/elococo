from django.core.management.base import BaseCommand
from django.db import transaction

from sale.bdd_calculations import default_ordered_annotation_format
from sale.models import Ordered


class Command(BaseCommand):
    help = 'Update the database for clean orders'

    def handle(self, *args, **options):
        orders = Ordered.objects.annotate(
            **default_ordered_annotation_format()
        ).filter(
            ordered_is_ready_to_delete=True
        ).prefetch_related("from_ordered", "from_ordered__to_product")

        count = orders.count()
        self.stdout.write(self.style.WARNING(
            f"There is {count} no valid to delete."
        ))

        with transaction.atomic():
            orders.delete()

        self.stdout.write(self.style.SUCCESS(
            f"There is {count} order(s) deleted."
        ))
