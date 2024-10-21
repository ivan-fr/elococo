import uuid

from django.conf import settings

from sale.bdd_calculations import default_ordered_annotation_format
from sale.models import Ordered


class BookingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.get(settings.BOOKING_SESSION_KEY, None) is not None:
            ordered_uuid = uuid.UUID(bytes=bytes(request.session.get(settings.BOOKING_SESSION_KEY, None)))

            query = Ordered.objects.annotate(
                **default_ordered_annotation_format()
            ).filter(pk=ordered_uuid)

            order = query.get()

            if not order.ordered_is_enable:
                del request.session[settings.BOOKING_SESSION_KEY]
                if request.session.get(settings.BOOKING_SESSION_FILL_KEY, None) is not None:
                    del request.session[settings.BOOKING_SESSION_FILL_KEY]
                if request.session.get(settings.BOOKING_SESSION_FILL_2_KEY, None) is not None:
                    del request.session[settings.BOOKING_SESSION_FILL_2_KEY]
                request.session.modified = True

        response = self.get_response(request)

        return response
