import uuid

from sale.forms import BOOKING_SESSION_KEY
from sale.models import Ordered


class BookingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.get(BOOKING_SESSION_KEY, None) is not None:
            ordered_uuid = uuid.UUID(bytes=bytes(request.session.get(BOOKING_SESSION_KEY, None)))
            if not Ordered.objects.filter(pk=ordered_uuid).exists():
                request.session[BOOKING_SESSION_KEY] = None
                request.session.modified = True

        response = self.get_response(request)

        return response
