import copy
from operator import methodcaller

from django.http import JsonResponse, Http404
from django.middleware.csrf import get_token
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import FormMixin
from django.views.generic.list import BaseListView

from catalogue.bdd_calculations import price_annotation_format, filled_category, total_price_from_all_product
from catalogue.forms import AddToBasketForm, UpdateBasketForm, ProductFormSet, BASKET_SESSION_KEY, \
    MAX_BASKET_PRODUCT, PRODUCT_INSTANCE_KEY
from elococo.generic import FormSetMixin
from catalogue.models import Category, Product


def update_basket_session(session, form, change=False):
    product = getattr(form, PRODUCT_INSTANCE_KEY)

    if form.cleaned_data.get("remove", False):
        if session.get(BASKET_SESSION_KEY, None) is None:
            return
        del session[BASKET_SESSION_KEY][product.slug]
        session.modified = True
        return

    if change:
        if session[BASKET_SESSION_KEY].get(product.slug, None) is not None:
            session[BASKET_SESSION_KEY][product.slug]["quantity"] = form.cleaned_data["quantity"]
            session.modified = True
        return

    if session.get(BASKET_SESSION_KEY, None) is None:
        session[BASKET_SESSION_KEY] = {product.slug: {
            "product_name": product.name,
            "quantity": form.cleaned_data["quantity"]
        }}
    else:
        if session[BASKET_SESSION_KEY].get(product.slug, None) is not None:
            session[BASKET_SESSION_KEY][product.slug]["quantity"] = \
                session[BASKET_SESSION_KEY][product.slug]["quantity"] + \
                form.cleaned_data["quantity"]
        else:
            session[BASKET_SESSION_KEY][product.slug] = {
                "product_name": product.name,
                "quantity": form.cleaned_data["quantity"]
            }
        session.modified = True


class BasketView(FormSetMixin, BaseListView):
    allow_empty = False
    template_name = 'catalogue/index_list.html'
    model = Product
    success_url = reverse_lazy("catalogue_basket")
    form_class = UpdateBasketForm
    formset_class = ProductFormSet
    factory_kwargs = {'extra': 0,
                      'absolute_max': MAX_BASKET_PRODUCT,
                      'max_num': MAX_BASKET_PRODUCT, 'validate_max': True,
                      'min_num': 1, 'validate_min': True,
                      'can_order': False,
                      'can_delete': False}

    def get_queryset(self):
        basket = self.request.session.get(BASKET_SESSION_KEY, {})

        if bool(basket):
            self.queryset = self.model.objects.filter(
                enable_sale=True, stock__gt=0)
            self.queryset = self.queryset.filter(slug__in=tuple(basket.keys()))
            self.queryset = self.queryset.annotate(
                **price_annotation_format(basket))[:MAX_BASKET_PRODUCT]
        else:
            self.queryset = None

        return super(BasketView, self).get_queryset()

    def get_factory_kwargs(self):
        kwargs = super(BasketView, self).get_factory_kwargs()
        basket = self.request.session.get(BASKET_SESSION_KEY, {})

        if bool(basket):
            basket_set = {product_slug for product_slug in basket.keys()}
            product_bdd_set = {product.slug for product in self.object_list}

            diff = basket_set.difference(product_bdd_set)

            if len(diff) > 0:
                for product_slug in diff:
                    del basket[product_slug]
                self.request.session[BASKET_SESSION_KEY] = basket
                self.request.session.modified = True

            for product in self.object_list:
                if product.effective_basket_quantity != basket[product.slug]["quantity"]:
                    if product.effective_basket_quantity <= 0:
                        del basket[product.slug]
                    else:
                        basket[product.slug]["quantity"] = product.effective_basket_quantity
                    self.request.session.modified = True

            self.initial = [{"quantity": basket[product_slug]["quantity"], "remove": False}
                            for product_slug in basket.keys()]

        kwargs["max_num"] = len(basket)
        return kwargs

    def get_formset_kwargs(self):
        basket = self.request.session.get(BASKET_SESSION_KEY, {})

        basket_enum = {product_slug: n for n,
                       product_slug in enumerate(basket.keys())}
        self.object_list = sorted(self.object_list, key=methodcaller(
            'compute_basket_oder', basket_enum=basket_enum))

        self.formset_kwargs = {
            "products_queryset": self.object_list, "session": self.request.session}
        return super(BasketView, self).get_formset_kwargs()

    def formset_valid(self, formset):
        for form in formset:
            update_basket_session(self.request.session, form, change=True)

        return super(BasketView, self).formset_valid(formset)

    def json_response(self, formset, basket):
        basket = copy.deepcopy(basket)
        aggregate = self.queryset.aggregate(*total_price_from_all_product())

        for i, product in enumerate(self.object_list):
            basket[product.slug].update({
                "input_html_quantity": str(formset[i]['quantity']),
                "input_html_remove": str(formset[i]['remove']),
                "price_exact_ttc_with_quantity": product.price_exact_ttc_with_quantity,
                "effective_reduction": product.effective_reduction,
                "price_exact_ttc": product.price_exact_ttc,
                "price_exact_ht": product.price_exact_ht,
                "form_errors": str(formset[i].errors)
            })
        basket["__all__"] = aggregate
        basket["formset_management"] = str(formset.management_form)
        basket["csrf_token"] = get_token(self.request)

        return JsonResponse(basket)

    def init_queryset(self):
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                if self.request.is_ajax():
                    return JsonResponse({})
                raise Http404(_('Empty list and “%(class_name)s.allow_empty” is False.') % {
                    'class_name': self.__class__.__name__,
                })

        return None

    def base_logical_response(self):
        if not self.request.is_ajax():
            raise Http404()

        basket = self.request.session.get(BASKET_SESSION_KEY, {})

        if not bool(basket):
            return JsonResponse({})

        response = self.init_queryset()
        if response is not None:
            return response

        return None

    def get(self, request, *args, **kwargs):
        response = self.base_logical_response()
        if response is not None:
            return response

        formset = self.construct_formset()
        return self.json_response(formset, self.request.session.get(BASKET_SESSION_KEY, {}))

    def post(self, request, *args, **kwargs):
        response = self.base_logical_response()
        if response is not None:
            return response

        formset = self.construct_formset()

        if formset.is_valid():
            return self.formset_valid(formset)
        else:
            return self.json_response(formset, self.request.session.get(BASKET_SESSION_KEY, {}))


class IndexView(ListView):
    paginate_by = 15
    template_name = 'catalogue/index_list.html'
    model = Product
    extra_context = {}

    def get_queryset(self):
        self.queryset = self.model.objects.filter(
            enable_sale=True, stock__gt=0)
        category_slug = self.kwargs.get('slug_category', None)
        self.extra_context.update(filled_category(5, category_slug))
        self.extra_context.update({"index": category_slug})

        if category_slug is not None:
            self.extra_context.update(
                {"filter_list": Category.get_annotated_list(self.extra_context["selected_category_root"], 2)}
            )

        if category_slug is not None:
            self.queryset = self.queryset.filter(
                categories__slug=category_slug)

        self.queryset = self.queryset.filter(stock__gt=0)
        self.queryset = self.queryset.annotate(**price_annotation_format())

        return super(IndexView, self).get_queryset()


class ProductDetailView(FormMixin, DetailView):
    form_class = AddToBasketForm
    model = Product
    template_name = 'catalogue/product_detail.html'
    slug_url_kwarg = 'slug_product'
    slug_field = 'slug'

    def get_queryset(self):
        self.queryset = self.model.objects.filter(
            enable_sale=True, stock__gt=0)
        self.queryset = self.queryset.annotate(**price_annotation_format())
        return super(ProductDetailView, self).get_queryset()

    def get_success_url(self):
        return reverse("catalogue_product_detail", kwargs={"slug_product": self.object.slug})

    def get_initial(self):
        initial = super(ProductDetailView, self).get_initial()
        initial.update({
            "product_slug": self.object.slug
        })
        return initial

    def get_form_kwargs(self):
        kwargs = super(ProductDetailView, self).get_form_kwargs()
        kwargs.update({"session": self.request.session,
                      PRODUCT_INSTANCE_KEY: self.object})
        return kwargs

    def form_valid(self, form):
        session = self.request.session
        update_basket_session(session, form)
        session["basket_updated"] = True
        return super(ProductDetailView, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        updated = self.request.session.get("basket_updated", False)
        self.extra_context = {"basket_updated": updated}

        if updated:
            self.request.session["basket_updated"] = False

        context = self.get_context_data(object=self.object)
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


class IndexRedirectionView(RedirectView):
    pattern_name = "catalogue_index"
