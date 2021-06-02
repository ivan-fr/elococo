import logging
import uuid

# Get an instance of a logger
logger = logging.getLogger(__name__)
from django.conf import settings
from paypal.standard.ipn.signals import valid_ipn_received
from paypal.standard.models import ST_PP_COMPLETED

from sale.models import Ordered


def show_me_the_money(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        if ipn_obj.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
            return

        queryset = Ordered.objects.filter(uuid.UUID(ipn_obj.invoice))
        try:
            order = queryset.get()
            price = order.price_exact_ttc_with_quantity_sum

            if ipn_obj.mc_gross == price and ipn_obj.mc_currency == 'EUR':
                order.payment_status = True
                order.save()
        except queryset.model.DoesNotExist:
            return
    else:
        logger.debug('Paypal payment status not completed: %s' % ipn_obj.payment_status)


valid_ipn_received.connect(show_me_the_money)
