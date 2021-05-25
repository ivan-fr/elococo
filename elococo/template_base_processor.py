from django.conf import settings
import random


def template_base_processor(request):
    return {'website_title': settings.WEBSITE_TITLE,
            'random_footer_logo': f'images/logo_{random.randint(2, 3)}.png'}
