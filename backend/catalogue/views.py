from operator import methodcaller

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin, FormView

from catalogue.bdd_calculations import (
    price_annotation_format, filled_category, get_related_products,
    total_price_from_all_product,
    data_from_all_product, cast_annotate_to_float, stock_sold, post_price_annotation_format
)
from catalogue.forms import AddToBasketForm, UpdateBasketForm, ProductFormSet, PromoForm
from catalogue.models import Product, Category
from elococo.generic import FormSetMixin
from sale.bdd_calculations import get_promo


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def update_basket_session(session, form, set_quantity=False):
    product = getattr(form, settings.PRODUCT_INSTANCE_KEY)

    if form.cleaned_data.get("remove", False):
        if session.get(settings.BASKET_SESSION_KEY, None) is None:
            return
        del session[settings.BASKET_SESSION_KEY][product.slug]
        session.modified = True
        return

    if set_quantity:
        if session[settings.BASKET_SESSION_KEY].get(product.slug, None) is not None:
            session[settings.BASKET_SESSION_KEY][product.slug]["quantity"] = form.cleaned_data["quantity"]
            session.modified = True
        return

    if session.get(settings.BASKET_SESSION_KEY, None) is None:
        session[settings.BASKET_SESSION_KEY] = {
            product.slug: {
                "product_name": product.name,
                "quantity": form.cleaned_data["quantity"]
            }
        }
    else:
        if session[settings.BASKET_SESSION_KEY].get(product.slug, None) is not None:
            session[settings.BASKET_SESSION_KEY][product.slug]["quantity"] = \
                session[settings.BASKET_SESSION_KEY][product.slug]["quantity"] + \
                form.cleaned_data["quantity"]
        else:
            session[settings.BASKET_SESSION_KEY][product.slug] = {
                "product_name": product.name,
                "quantity": form.cleaned_data["quantity"]
            }
        session.modified = True


class PromoBasketView(FormView):
    form_class = PromoForm

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "form_promo": render_to_string("catalogue/promo.html", self.get_context_data(), request)
        })

    def get_form_kwargs(self):
        kwargs = super(PromoBasketView, self).get_form_kwargs()
        kwargs.update({"session": self.request.session})
        return kwargs

    def post(self, request, *args, **kwargs):
        if not is_ajax(request):
            return HttpResponseForbidden()
        return super(PromoBasketView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        if form.cleaned_data.get("code_promo", None) is not None:
            self.request.session[settings.PROMO_SESSION_KEY] = {"code_promo": form.cleaned_data["code_promo"].code}
            self.request.session.modified = True
        return JsonResponse({})

    def form_invalid(self, form):
        return JsonResponse({
            "form_promo": render_to_string("catalogue/promo.html", self.get_context_data(), self.request),
        })


def product_to_exclude_(self, basket):
    basket_set = {product_slug for product_slug in basket.keys()}
    product_bdd_set = {product.slug for product in self.object_list}

    product_to_exclude = basket_set.difference(product_bdd_set)

    if len(product_to_exclude) > 0:
        for product_slug in product_to_exclude:
            del basket[product_slug]
        self.request.session[settings.BASKET_SESSION_KEY] = basket
        self.request.session.modified = True

    for product in self.object_list:
        if product.effective_basket_quantity != basket[product.slug]["quantity"]:
            basket[product.slug]["quantity"] = product.effective_basket_quantity
            self.request.session.modified = True

    self.object_list = filter(
        lambda product_filter: product_filter.slug not in product_to_exclude, self.object_list
    )

    return product_to_exclude


def get_basket_queryset(model, basket):
    return model.enable_objects.annotate(
        **stock_sold()
    ).filter(
        slug__in=tuple(basket.keys())
    ).annotate(
        **price_annotation_format(basket)
    ).annotate(
        **post_price_annotation_format()
    )


def check_promo(request, basket):
    promo_session = request.session.get(settings.PROMO_SESSION_KEY, {})
    promo_db = get_promo(basket, promo_session.get("code_promo", None))

    if promo_db is None and request.session.get(settings.PROMO_SESSION_KEY, None) is not None:
        del request.session[settings.PROMO_SESSION_KEY]

    return promo_db


class BasketSurfaceView(ListView):
    allow_empty = True
    model = Product

    def get_queryset(self):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})
        self.queryset = get_basket_queryset(self.model, basket)

        return super(BasketSurfaceView, self).get_queryset()

    def response_(self):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        promo_db = check_promo(self.request, basket)

        self.product_to_exclude = product_to_exclude_(self, basket)

        aggregate = self.queryset.exclude(
            slug__in=self.product_to_exclude
        ).aggregate(
            **total_price_from_all_product(promo=promo_db)
        )

        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        context = {
            "products": list(self.object_list),
            "aggregate": aggregate,
            "promo": promo_db,
            "basket": basket
        }

        context_ = {
            "html": render_to_string(
                "catalogue/basket_surface.html",
                context,
                self.request
            )
        }

        return JsonResponse(context_)

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return self.response_()


class BasketView(FormSetMixin, ListView):
    allow_empty = True
    template_name = 'catalogue/basket.html'
    model = Product
    success_url = reverse_lazy("catalogue_basket")
    form_class = UpdateBasketForm
    formset_class = ProductFormSet
    factory_kwargs = {'extra': 0,
                      'absolute_max': settings.MAX_BASKET_PRODUCT,
                      'max_num': settings.MAX_BASKET_PRODUCT, 'validate_max': True,
                      'min_num': 1, 'validate_min': True,
                      'can_order': False,
                      'can_delete': False}

    def get_queryset(self):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        self.queryset = self.model.enable_objects.annotate(
            **stock_sold()
        ).filter(
            slug__in=tuple(basket.keys())
        ).annotate(
            **price_annotation_format(basket)
        ).annotate(
            **post_price_annotation_format()
        )

        return super(BasketView, self).get_queryset()

    def get_factory_kwargs(self):
        kwargs = super(BasketView, self).get_factory_kwargs()
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        self.product_to_exclude = product_to_exclude_(self, basket)

        self.initial = [
            {"quantity": basket[product_slug]["quantity"], "remove": False}
            for product_slug in basket.keys()
        ]

        kwargs["max_num"] = len(basket)

        return kwargs

    def get_formset_kwargs(self):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        basket_enum = {product_slug: n for n, product_slug in enumerate(basket.keys())}
        self.object_list = sorted(
            self.object_list, key=methodcaller('compute_basket_oder', basket_enum=basket_enum)
        )

        self.formset_kwargs = {
            "products_queryset": self.object_list, "session": self.request.session
        }
        return super(BasketView, self).get_formset_kwargs()

    def formset_valid(self, formset):
        for form in formset:
            update_basket_session(self.request.session, form, set_quantity=True)

        return super(BasketView, self).formset_valid(formset)

    def response_(self, formset):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})
        promo_db = check_promo(self.request, basket)

        aggregate = self.queryset.exclude(
            slug__in=self.product_to_exclude
        ).aggregate(
            **total_price_from_all_product(promo=promo_db)
        )

        context = {
            "zip_products": list(zip(self.object_list, formset)),
            "aggregate": aggregate,
            "formset": formset,
            "promo": promo_db,
            "basket_view": True
        }

        return self.render_to_response(context)

    def init_queryset(self):
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                raise Http404(_('Empty list and “%(class_name)s.allow_empty” is False.') % {
                    'class_name': self.__class__.__name__,
                })

    def get(self, request, *args, **kwargs):
        self.init_queryset()
        formset = self.construct_formset()
        return self.response_(formset)

    def post(self, request, *args, **kwargs):
        self.init_queryset()
        formset = self.construct_formset()

        if formset.is_valid():
            return self.formset_valid(formset)
        else:
            return self.response_(formset)


class IndexView(ListView):
    paginate_by = 2
    template_name = 'catalogue/index_list.html'
    model = Product
    extra_context = {}

    def get_queryset(self):
        queryset = self.model.enable_objects.prefetch_related(
            "productimage_set"
        ).annotate(
            **stock_sold()
        )
        category_slug = self.kwargs.get('slug_category', None)

        if is_ajax(self.request):
            if category_slug is not None:
                selected_category = Category.objects.filter(slug=category_slug).get()
                self.extra_context.update(
                    {
                        "related_products": get_related_products(selected_category, products_queryset=queryset)
                    }
                )
        else:
            self.extra_context.update(
                filled_category(5, category_slug, products_queryset=queryset)
            )
        self.extra_context.update({"index": category_slug})
        selected_category_root = self.extra_context.get("selected_category_root", None)

        if selected_category_root is not None:
            self.extra_context.update({"index": selected_category_root.slug})

        if self.extra_context.get("related_products", None) is not None:
            queryset = self.extra_context["related_products"]
            self.extra_context["related_products"] = None

        annotation_p = price_annotation_format()
        cast_annotate_to_float(annotation_p, "price_exact_ttc")

        queryset = queryset.annotate(**annotation_p)
        self.extra_context.update(queryset.aggregate(*data_from_all_product()))

        if category_slug is None:
            url_name = "catalogue_index"
            self.extra_context.update({"current_url": reverse(url_name)})
        else:
            url_name = "catalogue_navigation_categories"
            self.extra_context.update({"current_url": reverse(url_name, kwargs={"slug_category": category_slug})})

        if self.request.GET.get("min_ttc_price", None) is not None \
                and self.request.GET.get("max_ttc_price", None) is not None:
            queryset = queryset.filter(
                price_exact_ttc__range=(
                    float(self.request.GET["min_ttc_price"]) - 1e-1,
                    float(self.request.GET["max_ttc_price"]) + 1e-1
                )
            )

        if self.request.GET.get("order", None) is not None:
            if self.request.GET["order"].lower() == "asc":
                self.ordering = ("price_exact_ttc",)
                self.extra_context.update({"order": 0})
            elif self.request.GET["order"].lower() == "desc":
                self.ordering = ("-price_exact_ttc",)
                self.extra_context.update({"order": 1})
        else:
            self.extra_context.update({"order": -1})

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                raise Http404(_('Empty list and “%(class_name)s.allow_empty” is False.') % {
                    'class_name': self.__class__.__name__,
                })
        context = self.get_context_data()

        if is_ajax(request):
            return JsonResponse({"html": render_to_string("catalogue/products_list.html", context, request)})

        return self.render_to_response(context)


class ProductDetailView(FormMixin, DetailView):
    form_class = AddToBasketForm
    model = Product
    template_name = 'catalogue/product_detail.html'
    slug_url_kwarg = 'slug_product'
    slug_field = 'slug'

    def get_queryset(self):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        self.queryset = self.model.enable_objects.prefetch_related(
            'categories', "productimage_set"
        ).annotate(
            **price_annotation_format(basket)
        )
        return super(ProductDetailView, self).get_queryset()

    def get_success_url(self):
        return reverse("catalogue_product_detail", kwargs={"slug_product": self.object.slug})

    def get_form_kwargs(self):
        kwargs = super(ProductDetailView, self).get_form_kwargs()
        kwargs.update({"session": self.request.session,
                       settings.PRODUCT_INSTANCE_KEY: self.object})
        return kwargs

    def form_valid(self, form):
        update_basket_session(self.request.session, form)
        messages.success(
            self.request,
            "Article correctement ajouté dans votre panier."
        )
        return super(ProductDetailView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        images = self.object.productimage_set.all()
        return super(ProductDetailView, self).get_context_data(object=self.object, images=images)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
