from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import FormMixin
from django.views.generic.list import BaseListView
from catalogue.models import Product
from catalogue.bdd_calculations import price_annotation_format, filled_category, total_price_from_all_product
from catalogue.forms import AddToBasketForm, BASKET_SESSION_KEY, MAX_BASKET_PRODUCT
from django.urls import reverse
from django.http import JsonResponse, Http404
from django.utils.translation import gettext as _


class BasketView(BaseListView):
    allow_empty = False
    template_name = 'catalogue/index_list.html'
    model = Product

    def get_queryset(self):
        basket = self.request.session.get(BASKET_SESSION_KEY, {})
        self.queryset = self.model.objects.filter(enable_sale=True)
        self.queryset = self.queryset.filter(slug__in=tuple(basket.keys()))
        self.queryset = self.queryset.annotate(**price_annotation_format(basket)) \
                            .annotate(total_price_from_all_product())[:MAX_BASKET_PRODUCT]

        return super(BasketView, self).get_queryset()

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404()

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
                if request.is_ajax():
                    return JsonResponse({})
                raise Http404(_('Empty list and “%(class_name)s.allow_empty” is False.') % {
                    'class_name': self.__class__.__name__,
                })

        basket = self.request.session.get(BASKET_SESSION_KEY, {})

        for product in self.object_list:
            basket[product.slug].update({
                "exact_price_with_quantity": product.exact_price_with_quantity,
                "exact_price_with_quantity__sum": product.exact_price_with_quantity__sum,
                "effective_reduction": product.effective_reduction,
                "exact_price": product.exact_price
            })

        return JsonResponse(basket)


class IndexView(ListView):
    paginate_by = 15
    allow_empty = False
    template_name = 'catalogue/index_list.html'
    model = Product
    extra_context = filled_category(5)

    def get_queryset(self):
        self.queryset = self.model.objects.filter(enable_sale=True)
        category_slug = self.kwargs.get('slug_category', None)
        self.extra_context.update({"index": category_slug})

        if category_slug is not None:
            self.queryset = self.queryset.filter(categories__slug=category_slug)

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
        self.queryset = self.model.objects.filter(stock__gt=0)
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
        kwargs.update({"session": self.request.session})
        return kwargs

    def form_valid(self, form):
        basket = self.request.session.get(BASKET_SESSION_KEY, None)

        if basket is None:
            self.request.session[BASKET_SESSION_KEY] = {form.cleaned_data["product_slug"]: {
                "product_name": self.object.name,
                "quantity": form.cleaned_data["quantity"]
            }}
        else:
            if self.request.session[BASKET_SESSION_KEY].get(form.cleaned_data["product_slug"], None) is not None:
                self.request.session[BASKET_SESSION_KEY][form.cleaned_data["product_slug"]]["quantity"] = \
                    self.request.session[BASKET_SESSION_KEY][form.cleaned_data["product_slug"]]["quantity"] \
                    + form.cleaned_data["quantity"]
            else:
                self.request.session[BASKET_SESSION_KEY][form.cleaned_data["product_slug"]] = {
                    "product_name": self.object.name,
                    "quantity": form.cleaned_data["quantity"]
                }
            self.request.session.modified = True

        return super(ProductDetailView, self).form_valid(form)

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
