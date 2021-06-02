from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseBadRequest, Http404, JsonResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView, BaseFormView, FormMixin

from catalogue.bdd_calculations import price_annotation_format, total_price_from_all_product
from catalogue.forms import BASKET_SESSION_KEY, MAX_BASKET_PRODUCT
from catalogue.models import Product
from sale.bdd_calculations import default_ordered_annotation_format
from sale.forms import OrderedForm, OrderedInformation, BOOKING_SESSION_KEY, BOOKING_SESSION_FILL_KEY, CheckoutForm
from sale.models import Ordered, OrderedProduct


@csrf_exempt
def payment_done(request, pk):
    return render(request, 'sale/payment_done.html', {"pk": pk})


@csrf_exempt
def payment_canceled(request, pk):
    return render(request, 'sale/payment_cancelled.html', {"pk": pk})


def get_object(self, queryset=None):
    if queryset is None:
        queryset = self.get_queryset()

    pk = self.kwargs[self.pk_url_kwarg]
    queryset = queryset.filter(pk=pk)

    try:
        obj = queryset.annotate(**default_ordered_annotation_format()).get()
    except queryset.model.DoesNotExist:
        raise Http404()
    return obj


class OrderedDetail(FormMixin, DetailView):
    model = Ordered
    form_class = CheckoutForm

    def get_object(self, queryset=None):
        obj = get_object(self, queryset)
        if obj.last_name is None:
            raise Http404()
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.session.get(BOOKING_SESSION_KEY, None) is None:
            return HttpResponseBadRequest()

        if self.object.pk.bytes != bytes(request.session[BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        client_token = settings.GATEWAY.client_token.generate({})

        context = self.get_context_data(object=self.object, client_token=client_token)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("sale:paypal_return", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        client_token = settings.GATEWAY.client_token.generate({})

        customer_kwargs = {
            "first_name": self.object.first_name,
            "last_name": self.object.last_name,
            "email": self.object.email,
            "phone": self.object.phone,
        }

        result = settings.GATEWAY.customer.create(customer_kwargs)
        if not result.is_success:
            context = self.get_context_data()
            context.update({
                'braintree_error': u'{} {}'.format(
                    result.message, 'Please get in contact.'),
                "client_token": client_token
            })
            return self.render_to_response(context)

        customer_id = result.customer.id

        address_dict = {
            "first_name": self.object.first_name,
            "last_name": self.object.last_name,
            "street_address": self.object.address,
            "extended_address": self.object.address2,
            "locality": self.object.city,
            "postal_code": self.object.postal_code,
            "country_name": 'France',
            "country_code_numeric": '250',
        }

        result = settings.GATEWAY.transaction.sale({
            "customer_id": customer_id,
            "amount": Decimal(self.object.price_exact_ttc_with_quantity_sum) * Decimal(1e-2),
            "payment_method_nonce": form.cleaned_data['payment_method_nonce'],
            "descriptor": {
                "name": settings.WEBSITE_TITLE,
            },
            "billing": address_dict,
            "shipping": address_dict,
            "options": {
                'store_in_vault_on_success': True,
                'submit_for_settlement': True,
            },
        })
        if not result.is_success:
            context = self.get_context_data()
            context.update({
                'braintree_error':
                    'Your payment could not be processed. Please check your'
                    ' input or use another payment method and try again.',
                "client_token": client_token
            })
            return self.render_to_response(context)

        self.object.payment_status = True
        self.object.save()
        return super(OrderedDetail, self).form_valid(form)

    def post(self, request, *args, **kwargs):
        nonce_from_the_client = self.request.POST.get("payment_method_nonce", None)
        if nonce_from_the_client is None:
            return HttpResponseBadRequest()

        self.object = self.get_object()

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class FillInformationOrdered(UpdateView):
    form_class = OrderedInformation
    model = Ordered
    template_name = "sale/ordered_fill_information.html"

    def get_object(self, queryset=None):
        return get_object(self, queryset)

    def get_success_url(self):
        return reverse("sale:detail", kwargs={"pk": self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.ordered_is_enable:
            return HttpResponseRedirect(reverse("sale:fill", self.object.pk))

        form = self.get_form()
        if form.is_valid():
            self.request.session[BOOKING_SESSION_FILL_KEY] = True
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        if 'form' not in kwargs and self.object.ordered_is_enable:
            kwargs['form'] = self.get_form()
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.session.get(BOOKING_SESSION_KEY, None) is None:
            return HttpResponseBadRequest()

        if self.object.pk.bytes != bytes(request.session[BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        return self.render_to_response(self.get_context_data())


class BookingBasketView(BaseFormView):
    form_class = OrderedForm
    model = Ordered

    def get_queryset(self):
        basket = self.request.session.get(BASKET_SESSION_KEY, {})

        if bool(basket):
            queryset = Product.objects.select_for_update().filter(enable_sale=True)
            queryset = queryset.filter(slug__in=tuple(basket.keys()))
            queryset = queryset.annotate(**price_annotation_format(basket))[:MAX_BASKET_PRODUCT]
        else:
            queryset = None

        return queryset

    def get_success_url(self):
        return reverse("sale:fill", kwargs={"pk": self.ordered.pk})

    def check_queryset(self):
        if self.product_list is None:
            return HttpResponseBadRequest()

        basket = self.request.session.get(BASKET_SESSION_KEY, {})

        basket_set = {product_slug for product_slug in basket.keys()}
        product_bdd_set = {product.slug for product in self.product_list}

        diff = basket_set.difference(product_bdd_set)

        if len(diff) > 0:
            return HttpResponseBadRequest()

        return None

    def form_valid(self, form):
        if self.request.session.get(BOOKING_SESSION_KEY, None) is not None:
            messages.warning(self.request,
                             'Vous avez déjà une commande en attente, une nouvelle reservation est impossible.')
            return JsonResponse({"reload": True})

        self.product_list = self.get_queryset()
        response = self.check_queryset()

        if response is not None:
            return response

        aggregate = self.get_queryset().aggregate(*total_price_from_all_product())
        basket = self.request.session.get(BASKET_SESSION_KEY, {})

        try:
            with transaction.atomic():
                self.ordered = Ordered.objects.create(
                    price_exact_ht_with_quantity_sum=int(
                        aggregate["price_exact_ht_with_quantity__sum"] * Decimal(100.)
                    ),
                    price_exact_ttc_with_quantity_sum=int(
                        aggregate["price_exact_ttc_with_quantity__sum"] * Decimal(100.)
                    )
                )

                ordered_product = []
                for product in self.product_list:
                    if product.effective_quantity != basket[product.slug]["quantity"]:
                        raise ValueError()

                    product.stock -= basket[product.slug]["quantity"]
                    ordered_product.append(
                        OrderedProduct(
                            from_ordered=self.ordered,
                            to_product=product,
                            product_name=product.name,
                            effective_reduction=product.effective_reduction,
                            price_exact_ht=int(product.price_exact_ht * Decimal(100.)),
                            price_exact_ttc=int(product.price_exact_ttc * Decimal(100.)),
                            price_exact_ht_with_quantity=int(product.price_exact_ht_with_quantity * Decimal(100.)),
                            price_exact_ttc_with_quantity=int(product.price_exact_ttc_with_quantity * Decimal(100.)),
                            quantity=basket[product.slug]["quantity"]
                        )
                    )
                Product.objects.bulk_update(self.product_list, ("stock",))
                OrderedProduct.objects.bulk_create(ordered_product)

            del self.request.session[BASKET_SESSION_KEY]
            self.request.session[BOOKING_SESSION_KEY] = list(self.ordered.pk.bytes)
            self.request.session.modified = True
        except ValueError:
            return HttpResponseBadRequest()

        messages.success(self.request, 'Votre panier a été correctement réservé.')
        return JsonResponse({"redirect": self.get_success_url()})

    def form_invalid(self, form):
        return JsonResponse({"form_errors": str(form.errors), "csrf_token": get_token(self.request)})

    def get(self, request, *args, **kwargs):
        if not self.request.is_ajax():
            raise Http404()

        return JsonResponse({"csrf_token": get_token(self.request)})
