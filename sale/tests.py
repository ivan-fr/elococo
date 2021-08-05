from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from elococo import get_dict_data_formset
from sale import get_amount
from elococo.settings import BACK_TWO_PLACES
from sale.models import DELIVERY_SPEED, Ordered
from django.conf import settings
from django.urls.base import reverse
from catalogue.models import Product
import random
from django.test import TestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

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

        if i > settings.MAX_BASKET_PRODUCT:
            continue


def setUp(self):
    for i, product in enumerate(self.setup_products, start=1):
        if i > settings.MAX_BASKET_PRODUCT:
            continue

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

    ordered_product_count = ordered.from_ordered.all().count()

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

    if settings.DELIVERY_FREE_GT < amount:
        self.assertIsNotNone(ordered.delivery_mode)
        self.assertIsNotNone(ordered.delivery_value)
    else:
        self.assertIsNotNone(ordered.delivery_mode)
        self.assertIsNone(ordered.delivery_value)


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


class SaleSeleniumTests(StaticLiveServerTestCase):
    fixtures = ["tests_dumpdata.yaml"]
    setup_products = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setUpTestData(cls)
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        setup = super().setUp()

        for i, product in enumerate(self.setup_products, start=1):
            if i > settings.MAX_BASKET_PRODUCT:
                continue

            response = self.client.post(
                reverse("catalogue_product_detail", kwargs={
                        "slug_product": product.slug}),
                {'quantity': random.randint(
                    1, min(settings.BASKET_MAX_QUANTITY_PER_FORM, STOCK))}
            )

            self.assertEqual(response.status_code, 302)

        return setup

    def test_post_ordered_detail(self):
        timeout = 5
        booking_basket(self)
        choose_delivery(self, False)
        fill(self, False)
        fill_next(self, False)

        ordered_queryset = get_ordered_queryset()
        ordered = ordered_queryset.order_by("createdAt").last()

        self.selenium.get(
            '%s%s' % (
                self.live_server_url,
                reverse("sale:detail", kwargs={'pk': ordered.pk})
            )
        )

        self.selenium.find_element_by_id('checkout-button').click()

        WebDriverWait(
            self.selenium, timeout
        ).until(
            lambda driver: driver.find_element_by_tag_name('body')
        )

        cardNumber = self.selenium.find_element_by_name("cardNumber")
        cardNumber.send_keys('4242 4242 4242 4242')

        cardExpiry = self.selenium.find_element_by_name("cardExpiry")
        cardExpiry.send_keys('04 / 24')
        
        cardCvc = self.selenium.find_element_by_name("cardCvc")
        cardCvc.send_keys('424')
        
        billingName = self.selenium.find_element_by_name("billingName")
        billingName.send_keys('The tester')
        
        self.selenium.find_element_by_css_selector('button[type=submit].SubmitButton').click()
