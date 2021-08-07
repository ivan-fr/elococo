from elococo import get_dict_data_formset
from sale import get_amount
from elococo import get_dict_data_formset
from sale import get_amount
from elococo.settings import BACK_TWO_PLACES
from sale.models import DELIVERY_SPEED, Ordered
from catalogue.models import Product
from django.conf import settings
from django.urls.base import reverse
from django.test import TestCase, LiveServerTestCase
from catalogue.models import Product
import random
import subprocess
import re
import os
import time
import stripe

STOCK = 10


def get_ordered_queryset():
    return Ordered.objects.prefetch_related(
        "order_address", "from_ordered", "from_ordered__to_product",
        "from_ordered__to_product__productimage_set"
    )


def setUpTestData(cls):
    for i in range(1, random.randint(2, 30)):
        cls.setup_products.append(
            Product.objects.create(
                name=i,
                description='description',
                price=i*10,
                TTC_price=False,
                enable_sale=True,
                stock=STOCK
            )
        )


def setUp(self):
    for i, product in enumerate(self.setup_products, start=1):
        if i > settings.MAX_BASKET_PRODUCT:
            break

        response = self.client.post(
            reverse("catalogue_product_detail", kwargs={
                    "slug_product": product.slug}),
            {'quantity': random.randint(
                1, min(settings.BASKET_MAX_QUANTITY_PER_FORM, STOCK))}
        )

        self.assertEqual(response.status_code, 302)


def booking_basket(self):
    ordered_queryset = get_ordered_queryset()
    order_count_before = ordered_queryset.count()

    response = self.client.post(
        reverse("sale:booking"),
        {}
    )

    order_count_after = ordered_queryset.count()
    ordered = ordered_queryset.order_by("createdAt").last()

    if ordered is not None:
        ordered_product_count = ordered.from_ordered.all().count()
    else:
        ordered_product_count = 0

    self.assertEqual(response.status_code, 200)
    self.assertEqual(order_count_after - 1, order_count_before)
    self.assertEqual(
        ordered_product_count,
        len(
            self.setup_products[:min(
                len(self.setup_products), settings.MAX_BASKET_PRODUCT
            )]
        )
    )


def choose_delivery(self, booking=True):
    if booking:
        self.test_booking_basket()

    ordered_queryset = get_ordered_queryset()
    ordered = ordered_queryset.order_by("createdAt").last()

    response = self.client.post(
        reverse("sale:delivery", kwargs={'pk': ordered.pk}),
        {'delivery_mode': DELIVERY_SPEED}
    )

    self.assertEqual(response.status_code, 302)

    ordered = ordered_queryset.order_by("createdAt").last()

    amount = get_amount(ordered, with_promo=False) * BACK_TWO_PLACES
    amount = amount.quantize(BACK_TWO_PLACES)

    if settings.DELIVERY_FREE_GT <= amount:
        self.assertIsNotNone(ordered.delivery_mode)
        self.assertIsNone(ordered.delivery_value)
    else:
        self.assertIsNotNone(ordered.delivery_mode)
        self.assertIsNotNone(ordered.delivery_value)


def fill(self, booking=True):
    if booking:
        self.test_booking_basket()

    ordered_queryset = get_ordered_queryset()
    ordered = ordered_queryset.order_by("createdAt").last()

    response = self.client.post(
        reverse("sale:fill", kwargs={'pk': ordered.pk}),
        {'phone': "0101010101", 'email': 'example@example.com'}
    )

    self.assertEqual(response.status_code, 302)

    ordered = ordered_queryset.order_by("createdAt").last()

    self.assertIsNotNone(ordered.email)
    self.assertIsNotNone(ordered.phone)


def fill_next(self, booking=True):
    if booking:
        self.test_booking_basket()

    ordered_queryset = get_ordered_queryset()
    ordered = ordered_queryset.order_by("createdAt").last()

    response = self.client.get(
        reverse("sale:fill_next", kwargs={'pk': ordered.pk})
    )

    self.assertEqual(response.status_code, 200)

    context = response.context_data
    formset = context['formset']

    for form in formset:
        for field in form:
            if field.name == "postal_code":
                field.initial = 75010
            elif field.name == "id":
                field.initial = ""
            else:
                field.initial = "address"

    data = get_dict_data_formset(formset)

    response = self.client.post(
        reverse("sale:fill_next", kwargs={'pk': ordered.pk}),
        data
    )

    self.assertEqual(response.status_code, 302)

    ordered = ordered_queryset.order_by("createdAt").last()
    address = ordered.order_address.all()[0]

    self.assertEqual(address.first_name, "address")
    self.assertEqual(address.last_name, "address")
    self.assertEqual(address.address, "address")
    self.assertEqual(address.address2, "address")
    self.assertEqual(address.postal_code, 75010)
    self.assertEqual(address.city, "address")


class SaleTests(TestCase):
    fixtures = ["tests_dumpdata.yaml"]
    setup_products = []

    @classmethod
    def setUpTestData(cls):
        setUpTestData(cls)

    def setUp(self):
        setup = super().setUp()
        setUp(self)

        return setup

    def test_booking_basket(self):
        booking_basket(self)

    def test_choose_delivery(self, booking=True):
        choose_delivery(self, booking)

    def test_fill(self, booking=True):
        fill(self,  booking)

    def test_fill_next(self, booking=True):
        fill_next(self, booking)

    def test_ordered_detail(self):
        self.test_booking_basket()
        self.test_choose_delivery(False)
        self.test_fill(False)
        self.test_fill_next(False)

        ordered_queryset = get_ordered_queryset()
        ordered = ordered_queryset.order_by("createdAt").last()

        response = self.client.get(
            reverse("sale:detail", kwargs={'pk': ordered.pk})
        )

        self.assertEqual(response.status_code, 200)


def run_stripe_triggers(self, ordered):
    stripe_private_key = os.getenv('STRIPE_PRIVATE_KEY')
    self.assertIsNotNone(stripe_private_key)

    process = subprocess.Popen(
        [settings.BASE_DIR / 'stripe', 'listen', '--api-key', stripe_private_key, '--forward-to', '%s%s' % (
            self.live_server_url,
            reverse("sale:webhook")
        )],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )

    for line in iter(process.stderr.readline, b''):
        line = line.decode("utf-8").strip()

        if line.startswith("Ready"):
            settings.STRIPE_WEBHOOK = re.search(
                r'^.*(whsec_[\w]+).*$', line).group(1)
            break

    os.environ['STRIPE_FIXTURE_ORDER_PK'] = str(ordered.pk)

    process_stripe_fixture = subprocess.Popen(
        [settings.BASE_DIR / 'stripe', 'fixtures', '--api-key', stripe_private_key,
            settings.BASE_DIR / 'sale' / 'fixtures' / 'stripe.json'],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )
    process_stripe_fixture.wait()

    time.sleep(10)

    process.terminate()


class LiveSaleTests(LiveServerTestCase):
    setup_products = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        stripe.api_key = os.getenv('STRIPE_PRIVATE_KEY')

    def setUp(self):
        setup = super().setUp()

        self.setup_products = []
        setUpTestData(self)
        self.assertGreater(len(self.setup_products), 0)
        setUp(self)

        return setup

    def test_post_ordered_detail_success(self):
        booking_basket(self)
        choose_delivery(self, False)
        fill(self, False)
        fill_next(self, False)

        ordered_queryset = get_ordered_queryset()
        ordered = ordered_queryset.order_by("createdAt").last()

        run_stripe_triggers(self, ordered)

        ordered = ordered_queryset.order_by("createdAt").last()
        self.assertTrue(ordered.payment_status)

        response = self.client.get(
            reverse("sale:payment_return", kwargs={
                    "pk": ordered.pk, "secrets_": ordered.secrets})
        )

        self.assertEqual(response.status_code, 200)

    def test_post_ordered_detail_fail(self):
        booking_basket(self)
        choose_delivery(self, False)
        fill(self, False)
        fill_next(self, False)

        ordered_queryset = get_ordered_queryset()
        ordered = ordered_queryset.order_by("createdAt").last()
        ordered.payment_status = True
        ordered.save()

        for product in Product.objects.all():
            product.stock = 0
            product.save()

        run_stripe_triggers(self, ordered)

        ordered = ordered_queryset.order_by("createdAt").last()
        self.assertFalse(ordered.payment_status)
