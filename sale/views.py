import secrets
import string
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponseBadRequest, Http404, JsonResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.template.loader import get_template
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView, BaseFormView, FormMixin, View
from django_weasyprint.views import WeasyTemplateView, WeasyTemplateResponseMixin

from catalogue.bdd_calculations import TVA_PERCENT
from catalogue.bdd_calculations import price_annotation_format, total_price_from_all_product
from catalogue.forms import BASKET_SESSION_KEY, MAX_BASKET_PRODUCT
from catalogue.models import Product
from elococo.generic import ModelFormSetView
from sale.bdd_calculations import default_ordered_annotation_format
from sale.forms import OrderedForm, OrderedInformation, BOOKING_SESSION_KEY, BOOKING_SESSION_FILL_KEY, CheckoutForm, \
    RetrieveOrderForm, BOOKING_SESSION_FILL_2_KEY, WIDGETS_FILL_NEXT, AddressFormSet
from sale.models import Ordered, OrderedProduct, Address, ORDER_SECRET_LENGTH

KEY_PAYMENT_ERROR = "payment_error"
PAYMENT_ERROR_NOT_PROCESS = 0
PAYMENT_ERROR_ORDER_NOT_ENABLED = 1
TWO_PLACES = Decimal(10) ** -2


class InvoiceView(WeasyTemplateView):
    template_name = "sale/invoice.html"
    pdf_stylesheets = [
        settings.STATICFILES_DIRS[0] / 'css/invoice.css',
    ]

    def get_context_data(self, **kwargs):
        try:
            order = Ordered.objects.filter(pk=kwargs["pk"], secrets=kwargs["secrets_"], payment_status=True).get()
            self.pdf_filename = f"invoice_{order.pk}"
            return super(InvoiceView, self).get_context_data(**{"ordered": order,
                                                                "tva": TVA_PERCENT,
                                                                "website_title": settings.WEBSITE_TITLE})
        except Ordered.DoesNotExist:
            raise Http404()


class PaymentDoneView(WeasyTemplateResponseMixin, View):
    template_name = "sale/invoice.html"
    pdf_stylesheets = [
        settings.STATICFILES_DIRS[0] / 'css/invoice.css',
    ]

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentDoneView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.session.get(BOOKING_SESSION_KEY, None) is None:
            raise Http404()

        try:
            order = Ordered.objects.filter(pk=kwargs["pk"], secrets=kwargs["secrets_"],
                                           payment_status=True).get()
        except Ordered.DoesNotExist:
            raise Http404()

        if order.pk.bytes != bytes(request.session[BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        del request.session[BOOKING_SESSION_KEY]
        if request.session.get(BOOKING_SESSION_FILL_KEY, None) is not None:
            del request.session[BOOKING_SESSION_FILL_KEY]
        if request.session.get(BOOKING_SESSION_FILL_2_KEY, None) is not None:
            del request.session[BOOKING_SESSION_FILL_2_KEY]

        htmly = get_template('sale/email_invoice.html')
        context_dict = {"ordered": order,
                        "tva": TVA_PERCENT,
                        "website_title": settings.WEBSITE_TITLE}
        pdf_response = self.render_to_response(context_dict).render()
        html_content = htmly.render(context_dict)
        email = EmailMessage(
            f"{settings.WEBSITE_TITLE} - FACTURE - Reçu de commande #{order.pk}",
            html_content,
            settings.EMAIL_HOST_USER,
            [order.email]
        )
        email.content_subtype = "html"
        email.attach(f"invoice_#{order.pk}", pdf_response.getvalue(), 'application/pdf')
        email.send()

        return render(request, 'sale/payment_done.html', {"pk": order.pk, 'secrets': order.secrets})


@csrf_exempt
def payment_canceled(request, pk):
    type_error = request.session.get(KEY_PAYMENT_ERROR, None)
    if type_error is None:
        return HttpResponseBadRequest()

    del request.session[KEY_PAYMENT_ERROR]

    return render(request, 'sale/payment_cancelled.html', {"pk": pk, "type_error": type_error})


def get_object(self, queryset=None, extra_filter=None):
    if queryset is None:
        queryset = self.get_queryset()

    pk = self.kwargs.get(self.pk_url_kwarg, None)
    if pk is not None:
        queryset = queryset.filter(pk=pk)

    if extra_filter is not None:
        queryset = queryset.filter(**extra_filter)

    try:
        obj = queryset.annotate(**default_ordered_annotation_format()).prefetch_related("order_address").get()
    except queryset.model.DoesNotExist:
        raise Http404()
    return obj


class RetrieveOrderedDetail(FormMixin, DetailView):
    model = Ordered
    form_class = RetrieveOrderForm
    template_name = "sale/retrieve_order.html"

    def get_object(self, queryset=None):
        return False

    def form_valid(self, form):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(self.get_context_data(form=form))

    def get_object_form(self, form, queryset=None):
        return get_object(self, queryset,
                          {"pk": form.cleaned_data["pk"], "secrets": form.cleaned_data["secrets"]})

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            self.object = self.get_object_form(form)
            return self.form_valid(form)
        else:
            self.object = self.get_object()
            return self.form_invalid(form)


class OrderedDetail(FormMixin, DetailView):
    model = Ordered
    form_class = CheckoutForm

    def get_object(self, queryset=None):
        obj = get_object(self, queryset)
        if obj.last_name is None:
            raise Http404()
        return obj

    def get(self, request, *args, **kwargs):
        if request.session.get(BOOKING_SESSION_FILL_KEY, None) is None:
            return HttpResponseBadRequest()

        if request.session.get(BOOKING_SESSION_FILL_2_KEY, None) is None:
            return HttpResponseBadRequest()

        if self.object.pk.bytes != bytes(request.session[BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()        
        
        self.object = self.get_object()

        if request.session.get(BOOKING_SESSION_KEY, None) is None:
            return HttpResponseBadRequest()

        if self.object.pk.bytes != bytes(request.session[BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        if not self.object.payment_status:
            client_token = settings.GATEWAY.client_token.generate({})
        else:
            client_token = None

        amount = Decimal(self.object.price_exact_ttc_with_quantity_sum) * Decimal(1e-2)
        context = self.get_context_data(object=self.object, client_token=client_token,
                                        amount=str(amount.quantize(TWO_PLACES)))
        return self.render_to_response(context)

    def get_invalid_url(self):
        return reverse("sale:paypal_cancel", kwargs={"pk": self.object.pk})

    def get_success_url(self):
        return reverse("sale:paypal_return", kwargs={"pk": self.object.pk, 'secrets_': self.object.secrets})

    def form_valid(self, form):
        customer_kwargs = {
            "first_name": self.object.first_name,
            "last_name": self.object.last_name,
            "email": self.object.email,
            "phone": self.object.phone,
        }

        if self.object.ordered_is_ready_to_delete:
            self.request.session[KEY_PAYMENT_ERROR] = PAYMENT_ERROR_ORDER_NOT_ENABLED
            return HttpResponseRedirect(self.get_invalid_url())

        result = settings.GATEWAY.customer.create(customer_kwargs)
        if not result.is_success:
            self.request.session[KEY_PAYMENT_ERROR] = PAYMENT_ERROR_NOT_PROCESS
            return HttpResponseRedirect(self.get_invalid_url())

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

        amount = Decimal(self.object.price_exact_ttc_with_quantity_sum) * Decimal(1e-2)

        result = settings.GATEWAY.transaction.sale({
            "customer_id": customer_id,
            "amount": amount.quantize(TWO_PLACES),
            "payment_method_nonce": form.cleaned_data['payment_method_nonce'],
            "descriptor": {
                "name": "company*my product",
                "phone": "0637728273",
                "url": "elococo.fr",
            },
            "billing": address_dict,
            "shipping": address_dict,
            "options": {
                'store_in_vault_on_success': True,
                'submit_for_settlement': True,
            },
        })

        if not result.is_success:
            self.request.session[KEY_PAYMENT_ERROR] = PAYMENT_ERROR_NOT_PROCESS
            return HttpResponseRedirect(self.get_invalid_url())

        with transaction.atomic():
            self.object.payment_status = True
            self.object.invoice_date = now()
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


class FillAddressInformationOrdered(ModelFormSetView):
    model = Address
    formset_class = AddressFormSet
    pk_url_kwarg = "pk"
    fields = ("first_name", "last_name", "address", "address2", "postal_code", "city")
    factory_kwargs = {'extra': 1,
                      'absolute_max': 2,
                      'max_num': 2, 'validate_max': True,
                      'min_num': 1, 'validate_min': True,
                      'can_order': False,
                      'can_delete': False}
    template_name = "sale/ordered_fill_information_next.html"

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs.update({"queryset":self.object_list, "ordered_queryset": self.object})
        return kwargs

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        kwargs.setdefault("widgets", WIDGETS_FILL_NEXT)
        return kwargs

    def get_object(self, queryset=None):
        return get_object(self, queryset=Ordered.objects)

    def get_success_url(self):
        return reverse("sale:detail", kwargs={"pk": self.object.pk})

    def formset_invalid(self, formset):
        return self.render_to_response(self.get_context_data(formset=formset, ordered=self.object))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.ordered_is_enable:
            return HttpResponseRedirect(reverse("sale:fill_next", self.object.pk))

        self.object_list = self.object.order_address.all()
        formset = self.construct_formset()
        if formset.is_valid():
            self.request.session[BOOKING_SESSION_FILL_2_KEY] = True
            return self.formset_valid(formset)
        else:
            return self.formset_invalid(formset)

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        if 'formset' in kwargs and not self.object.ordered_is_enable:
            del kwargs['formset']
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.session.get(BOOKING_SESSION_KEY, None) is None:
            return HttpResponseBadRequest()

        if self.object.pk.bytes != bytes(request.session[BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        self.object_list = self.object.order_address.all()
        formset = self.construct_formset()
        return self.render_to_response(self.get_context_data(formset=formset, ordered=self.object))


class FillInformationOrdered(UpdateView):
    form_class = OrderedInformation
    model = Ordered
    template_name = "sale/ordered_fill_information.html"

    def get_object(self, queryset=None):
        return get_object(self, queryset)

    def get_success_url(self):
        return reverse("sale:fill_next", kwargs={"pk": self.object.pk})

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
                    ),
                    secrets=''.join(secrets.choice(string.ascii_lowercase) for i in range(ORDER_SECRET_LENGTH))
                )

                ordered_product = []
                for product in self.product_list:
                    if product.effective_basket_quantity != basket[product.slug]["quantity"]:
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
                            price_exact_ttc_with_quantity=int(
                                product.price_exact_ttc_with_quantity * Decimal(100.)),
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
