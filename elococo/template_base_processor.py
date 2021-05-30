import random
import uuid

from django.conf import settings
from django.urls import reverse

from sale.forms import BOOKING_SESSION_KEY
from sale.models import Ordered


def template_base_processor(request):
    my_dict = {'website_title': settings.WEBSITE_TITLE,
               'random_footer_logo': f'images/logo_{random.randint(2, 3)}.png',
               'url_get_basket': reverse("catalogue_basket"),
               'url_get_booking': reverse("sale:booking"),
               'url_my_ordered': None}

    if request.session.get(BOOKING_SESSION_KEY, None) is not None:
        ordered_uuid = uuid.UUID(bytes=bytes(request.session[BOOKING_SESSION_KEY]))
        if not Ordered.objects.filter(pk=ordered_uuid).exists():
            request.session[BOOKING_SESSION_KEY] = None
            request.session.modified = True
        else:
            my_dict.update({
                'url_my_ordered':
                    reverse("sale:fill",
                            kwargs={"pk": ordered_uuid})
            })

    return my_dict
