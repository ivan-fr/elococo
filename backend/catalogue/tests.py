from elococo import get_dict_data_formset
import random

from sale.models import Promo
from django.conf import settings
from catalogue.bdd_calculations import cast_annotate_to_float, get_related_products, price_annotation_format
from catalogue.models import Category, Product
from django.test import TestCase
from django.urls import reverse


def test_pages(self, product_db, products_context, paginator):
    products_in_page = product_db[:paginator.per_page]
    last_page = paginator.page(paginator.num_pages)

    for i, product in enumerate(products_in_page):
        self.assertEqual(product.slug, products_context[i].slug)

    products_in_last_page = product_db[(
        paginator.num_pages - 1) * paginator.per_page:]

    for i, product in enumerate(products_in_last_page):
        self.assertEqual(product.slug, last_page[i].slug)


def test_orders(self, product_db, category_selected, order, field_order):
    response = self.client.get(reverse("catalogue_navigation_categories", kwargs={
                               "slug_category": category_selected.slug}) + "?order=" + order)
    context = response.context_data

    product_list_context = context['product_list']
    paginator = context['paginator']
    annotation_p = price_annotation_format()
    cast_annotate_to_float(annotation_p, "price_exact_ttc")

    asc_product_db = product_db.annotate(
        **annotation_p).order_by(field_order)[:paginator.per_page]
    zip_products = zip(asc_product_db, product_list_context)

    for asc_product, context_product in zip_products:
        self.assertEqual(asc_product.slug, context_product.slug)


class CatalogueTests(TestCase):
    fixtures = ["tests_dumpdata.yaml"]

    @classmethod
    def setUpTestData(cls):
        for i in range(1, random.randint(2, 30)):
            Product.objects.create(
                name=i,
                description='description',
                price=i*10,
                TTC_price=False,
                enable_sale=True,
                stock=10
            )

    def test_index(self):
        response = self.client.get(reverse("catalogue_index"))

        context = response.context_data

        product_db = Product.objects.all()
        product_list_context = context['product_list']
        paginator = context['paginator']

        test_pages(self, product_db, product_list_context, paginator)

        self.assertEqual(product_db.count(), paginator.count)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(context['selected_category_root'])
        self.assertIsNone(context['selected_category'])

        category_selected = Category.objects.first()
        product_db = get_related_products(category_selected, product_db)
        response = self.client.get(reverse("catalogue_navigation_categories", kwargs={
                                   "slug_category": category_selected.slug}))

        context = response.context_data

        selected_category = context['selected_category']
        product_list_context = context['product_list']
        paginator = context['paginator']

        self.assertEqual(selected_category.slug, category_selected.slug)
        self.assertEqual(response.status_code, 200)

        for product in product_list_context:
            list_bool = []

            for category in product.categories.all():
                list_bool.append(category.is_child_of(
                    category_selected) or category.slug == category_selected.slug)

            self.assertTrue(any(list_bool))

        test_pages(self, product_db, product_list_context, paginator)

        middle_ttc = (context['price_exact_ttc__min'] +
                      context['price_exact_ttc__max']) / 2.

        test_orders(self, product_db, category_selected,
                    "asc", "price_exact_ttc")
        test_orders(self, product_db, category_selected,
                    "desc", "-price_exact_ttc")

        response = self.client.get(reverse("catalogue_navigation_categories", kwargs={
                                   "slug_category": category_selected.slug}) + "?min_ttc_price=" + str(middle_ttc) + "&max_ttc_price=" + str(context['price_exact_ttc__max']))
        context = response.context_data

        product_list_context = context['product_list']
        all_supp_middle = []

        for product in product_list_context:
            all_supp_middle.append(product.price_exact_ttc >= middle_ttc)
            self.assertTrue(all(all_supp_middle))

    def test_detail(self):
        product_selected = Product.objects.first()

        response = self.client.get(reverse("catalogue_product_detail", kwargs={
                                   "slug_product": product_selected.slug}))
        context = response.context_data

        product_context = context['product']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(product_context.slug, product_selected.slug)

    def test_basket_surface(self):
        response = self.client.get(reverse("catalogue_basket_surface"))
        self.assertEqual(response.status_code, 200)

    def test_promo(self):
        promo = Promo.objects.first()
        response = self.client.post(
            reverse("catalogue_basket_promo"), {
                'code_promo': promo.pk
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_basket(self, product_selected=Product.objects.first):
        product_selected = product_selected()
        session = self.client.session
        basket_before = session.get(settings.BASKET_SESSION_KEY, {})
        quantity_before = basket_before.get(
            product_selected.slug, {'quantity': 0})['quantity']

        response = self.client.post(
            reverse("catalogue_product_detail", kwargs={
                    "slug_product": product_selected.slug}),
            {'quantity': 1}
        )
        self.assertEqual(response.status_code, 302)

        session = self.client.session
        basket_after = session.get(settings.BASKET_SESSION_KEY, {})
        quantity_after = basket_after.get(
            product_selected.slug, {'quantity': 0})['quantity']

        try:
            self.assertEqual(len(basket_after) - 1, len(basket_before))
        except AssertionError:
            self.assertEqual(quantity_after - 1, quantity_before)

    def test_basket(self):
        self.test_detail_basket()
        self.test_detail_basket(product_selected=Product.objects.last)

        response = self.client.get(reverse("catalogue_basket"))
        context = response.context_data
        session = self.client.session
        basket = session.get(settings.BASKET_SESSION_KEY, {})

        zip_products = context['zip_products']

        for product, _ in zip_products:
            self.assertTrue(basket.get(product.slug, False))

        self.assertEqual(response.status_code, 200)

    def test_basket_post(self):
        self.test_basket()

        response = self.client.get(
            reverse("catalogue_basket")
        )

        context = response.context_data
        formset = context['formset']

        for form in formset:
            for field in form:
                if field.name == 'remove':
                    field.initial = True

        data = get_dict_data_formset(formset)

        response = self.client.post(
            reverse("catalogue_basket"), data
        )

        session = self.client.session
        basket = session.get(settings.BASKET_SESSION_KEY, {})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(basket), 0)
