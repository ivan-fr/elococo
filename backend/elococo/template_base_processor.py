import random
import uuid

from django.conf import settings
from django.urls import reverse


def template_base_processor(request):
    basket = request.session.get(settings.BASKET_SESSION_KEY, {})

    my_dict = {
        'website_title': settings.WEBSITE_TITLE,
        'delivery_free_gt': settings.DELIVERY_FREE_GT,
        'random_footer_logo': f'images/logo_{random.randint(2, 3)}.png',
        'url_get_basket': reverse("catalogue_basket"),
        'url_get_booking': reverse("sale:booking"),
        'url_get_promo': reverse("catalogue_basket_promo"),
        'basket_len': sum((data["quantity"] for data in basket.values())),
        'url_my_ordered': None, 'url_my_ordered_fill_next': None, 'url_my_ordered_detail': None,
        "tva": settings.TVA_PERCENT,
    }

    if request.session.get(settings.BOOKING_SESSION_KEY, None) is not None:
        ordered_uuid = uuid.UUID(bytes=bytes(request.session[settings.BOOKING_SESSION_KEY]))

        my_dict.update({
            'url_my_ordered': reverse("sale:fill", kwargs={"pk": ordered_uuid})
        })

        if request.session.get(settings.BOOKING_SESSION_FILL_KEY, None) is not None:
            my_dict.update({
                'url_my_ordered_fill_next': reverse("sale:fill_next", kwargs={"pk": ordered_uuid})
            })

        if request.session.get(settings.BOOKING_SESSION_FILL_2_KEY, None) is not None:
            my_dict.update({
                'url_my_ordered_detail': reverse("sale:detail", kwargs={"pk": ordered_uuid})
            })

    return my_dict
