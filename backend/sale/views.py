import os
import secrets
import string
import uuid
from decimal import Decimal
from smtplib import SMTPAuthenticationError

import stripe
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.db import transaction
from django.http import HttpResponseBadRequest, Http404, JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import UpdateView, BaseFormView, FormMixin, View
from stripe.error import InvalidRequestError

from catalogue.bdd_calculations import (
    price_annotation_format, total_price_from_all_product, stock_sold, post_price_annotation_format
)
from catalogue.models import Product
from elococo.generic import ModelFormSetView
from elococo.settings import BACK_TWO_PLACES
from sale import get_amount
from sale.bdd_calculations import default_ordered_annotation_format, get_promo
from sale.forms import (
    AddressForm, OrderedForm, OrderedInformation, CheckoutForm, RetrieveOrderForm, AddressFormSet, DeliveryMode
)
from sale.models import Ordered, OrderedProduct, Address

KEY_PAYMENT_ERROR = "payment_error"
PAYMENT_ERROR_ORDER_NOT_ENABLED = 1
TWO_PLACES = Decimal(10) ** -2


@require_POST
@csrf_exempt
def webhook_view(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    if os.getenv('STRIPE_WEBHOOK_TEST') is not None:
        webhook = os.getenv('STRIPE_WEBHOOK_TEST')
    else:
        webhook = settings.STRIPE_WEBHOOK

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook
        )
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event["type"] == "payment_intent.amount_capturable_updated":
        session = event['data']['object']
        return capture_order(session)
    elif event['type'] == 'charge.captured':
        session = event['data']['object']
        return fulfill_order(request, session)
    elif event['type'] == 'payment_intent.canceled':
        session = event['data']['object']
        return cancel_order(session)

    return HttpResponse(status=404)


def cancel_order(session):
    try:
        ordered_uuid = uuid.UUID(session["metadata"]["pk_order"])
    except ValueError:
        ordered_uuid = None
    try:
        order = Ordered.objects.filter(
            pk=ordered_uuid,
        ).prefetch_related("order_address").get()

        if order.payment_status:
            raise ValueError()
    except Ordered.DoesNotExist:
        return HttpResponse(status=403)
    except ValueError:
        return HttpResponse(status=403)

    return HttpResponse(status=200)


def capture_order(session):
    cancel = False

    try:
        ordered_uuid = uuid.UUID(session["metadata"]["pk_order"])
    except ValueError:
        ordered_uuid = None
    except KeyError:
        ordered_uuid = None

    try:
        order = Ordered.objects.filter(
            pk=ordered_uuid
        ).prefetch_related(
            "from_ordered", "from_ordered__to_product"
        ).get()

        if order.payment_status:
            raise ValueError()
    except Ordered.DoesNotExist:
        return HttpResponse(status=403)
    except ValueError:
        return HttpResponse(status=403)

    try:
        products = set()

        for ordered_product in order.from_ordered.all():
            product = ordered_product.to_product
            product.stock -= ordered_product.quantity
            if product.stock < 0:
                raise ValueError()
            products.add(product)

        try:
            with transaction.atomic():
                Product.objects.bulk_update(list(products), ("stock",))
                order.payment_status = True
                order.invoice_date = now()
                order.save()
        except IntegrityError:
            cancel = True
    except ValueError:
        cancel = True

    if cancel:
        try:
            stripe.PaymentIntent.cancel(session["id"])
        except InvalidRequestError:
            pass
        return HttpResponse(status=400)

    stripe.PaymentIntent.capture(session["id"])
    return HttpResponse(status=200)


def fulfill_order(request, session):
    try:
        ordered_uuid = uuid.UUID(session["metadata"]["pk_order"])
    except ValueError:
        ordered_uuid = None

    try:
        order = Ordered.objects.filter(
            pk=ordered_uuid,
        ).prefetch_related("order_address").get()

        if not order.payment_status:
            raise ValueError()
    except Ordered.DoesNotExist:
        return HttpResponse(status=403)
    except ValueError:
        return HttpResponse(status=403)

    context_dict = {
        "ordered": order,
        "website_title": settings.WEBSITE_TITLE,
        "email": True
    }
    html_content = render_to_string("sale/invoice.html", context_dict, request)
    email = EmailMessage(
        f"{settings.WEBSITE_TITLE} - FACTURE - Reçu de commande #{order.pk}",
        html_content,
        settings.EMAIL_HOST_USER,
        [order.email, settings.EMAIL_HOST_USER]
    )
    email.content_subtype = "html"

    try:
        email.send()
    except SMTPAuthenticationError:
        pass

    return HttpResponse(status=200)


class InvoiceView(TemplateView):
    template_name = "sale/invoice.html"

    def get_context_data(self, **kwargs):
        try:
            order = Ordered.objects.filter(
                pk=kwargs["pk"],
                secrets=kwargs["secrets_"],
                payment_status=True
            ).get()
            return super(InvoiceView, self).get_context_data(
                **{
                    "ordered": order,
                    "tva": settings.TVA_PERCENT,
                    "website_title": settings.WEBSITE_TITLE
                }
            )
        except Ordered.DoesNotExist:
            raise Http404()


class PaymentDoneView(TemplateView, View):
    template_name = "sale/invoice.html"
    pdf_stylesheets = [
        settings.STATICFILES_DIRS[0] / 'css' / 'invoice.css',
    ]

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentDoneView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.session.get(settings.BOOKING_SESSION_KEY, None) is None:
            raise Http404()

        try:
            order = Ordered.objects.filter(
                pk=kwargs["pk"],
                secrets=kwargs["secrets_"],
            ).prefetch_related("order_address").get()
        except Ordered.DoesNotExist:
            raise Http404()

        if order.pk.bytes != bytes(request.session[settings.BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        del request.session[settings.BOOKING_SESSION_KEY]
        if request.session.get(settings.BOOKING_SESSION_FILL_KEY, None) is not None:
            del request.session[settings.BOOKING_SESSION_FILL_KEY]
        if request.session.get(settings.BOOKING_SESSION_FILL_2_KEY, None) is not None:
            del request.session[settings.BOOKING_SESSION_FILL_2_KEY]

        return render(request, 'sale/payment_done.html', {"pk": order.pk, 'secrets': order.secrets})


@csrf_exempt
def payment_canceled(request, pk):
    type_error = request.session.get(KEY_PAYMENT_ERROR, None)
    if type_error is not None:
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
        obj = queryset.annotate(
            **default_ordered_annotation_format()
        ).prefetch_related("order_address", "from_ordered", "from_ordered__to_product",
                           "from_ordered__to_product__productimage_set").get()
    except queryset.model.DoesNotExist:
        raise Http404()
    return obj


class RetrieveOrderedDetail(FormMixin, DetailView):
    model = Ordered
    form_class = RetrieveOrderForm
    template_name = "sale/retrieve_order.html"
    initial = {"attempt": False}

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
        if obj.order_address.first().last_name is None:
            raise Http404()
        return obj

    def get(self, request, *args, **kwargs):
        if request.session.get(settings.BOOKING_SESSION_KEY, None) is None:
            return HttpResponseBadRequest()

        if request.session.get(settings.BOOKING_SESSION_FILL_KEY, None) is None:
            return HttpResponseBadRequest()

        if request.session.get(settings.BOOKING_SESSION_FILL_2_KEY, None) is None:
            return HttpResponseBadRequest()

        self.object = self.get_object()

        amount = get_amount(self.object, with_delivery=False)
        amount *= settings.BACK_TWO_PLACES

        if self.object.delivery_mode is None and settings.DELIVERY_FREE_GT < amount:
            return HttpResponseRedirect(reverse("sale:delivery", kwargs={"pk": self.object.pk}))

        if self.object.pk.bytes != bytes(request.session[settings.BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        if not self.object.payment_status and self.object.ordered_is_enable:
            public_api_key = settings.STRIPE_PUBLIC_KEY
        else:
            public_api_key = None

        context = self.get_context_data(
            object=self.object, public_api_key=public_api_key,
            amount=str(
                (get_amount(self.object, with_delivery=True) *
                 settings.BACK_TWO_PLACES).quantize(TWO_PLACES)
            )
        )
        return self.render_to_response(context)

    def get_invalid_url(self):
        return reverse("sale:payment_cancel", kwargs={"pk": self.object.pk})

    def get_success_url(self):
        return reverse("sale:payment_return", kwargs={"pk": self.object.pk, 'secrets_': self.object.secrets})

    def form_valid(self, form):
        if self.object.ordered_is_ready_to_delete:
            self.request.session[KEY_PAYMENT_ERROR] = PAYMENT_ERROR_ORDER_NOT_ENABLED
            return JsonResponse({"redirect": self.get_invalid_url()})

        amount = get_amount(self.object, with_delivery=False)
        amount *= settings.BACK_TWO_PLACES

        if self.object.delivery_mode is None and settings.DELIVERY_FREE_GT < amount:
            return HttpResponseRedirect(reverse("sale:delivery", kwargs={"pk": self.object.pk}))

        images = []

        for ordered_product in self.object.from_ordered.all():
            product = ordered_product.to_product

            try:
                if product.productimage_set.all()[0].url_host is not None:
                    images.append(product.productimage_set.all()[0].url_host)
                else:
                    image_url = product.productimage_set.all()[0].image.url
                    images.append(self.request.build_absolute_uri(image_url))
            except IndexError:
                continue

        images = images[:8]

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'eur',
                            'unit_amount_decimal': get_amount(self.object, with_delivery=True).quantize(TWO_PLACES),
                            'product_data': {
                                'name': f'Order #{self.object.pk}',
                                'images': images
                            },
                        },
                        'quantity': 1,
                    },
                ],
                payment_intent_data={
                    "capture_method": "manual",
                    "metadata": {
                        "pk_order": self.object.pk
                    }
                },
                metadata={
                    "pk_order": self.object.pk
                },
                customer_email=self.object.email,
                mode='payment',
                success_url=self.request.build_absolute_uri(
                    self.get_success_url()),
                cancel_url=self.request.build_absolute_uri(
                    self.get_invalid_url()),
            )

            return JsonResponse({"id": checkout_session.id})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return JsonResponse({"error": list(form.errors)})


class FillAddressInformationOrdered(ModelFormSetView):
    model = Address
    formset_class = AddressFormSet
    form_class = AddressForm
    pk_url_kwarg = "pk"
    fields = (
        "first_name", "last_name", "address",
        "address2", "postal_code", "city"
    )
    factory_kwargs = {
        'extra': 1,
        'absolute_max': 2,
        'max_num': 2, 'validate_max': True,
        'min_num': 1, 'validate_min': True,
        'can_order': False,
        'can_delete': False
    }
    template_name = "sale/ordered_fill_information_next.html"

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs.update({"queryset": self.object_list,
                       "ordered_queryset": self.object})
        return kwargs

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        return kwargs

    def get_object(self, queryset=None):
        return get_object(self, queryset=Ordered.objects.all())

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
            self.request.session[settings.BOOKING_SESSION_FILL_2_KEY] = True
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

        if request.session.get(settings.BOOKING_SESSION_KEY, None) is None:
            return HttpResponseBadRequest()

        if self.object.pk.bytes != bytes(request.session[settings.BOOKING_SESSION_KEY]):
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
            self.request.session[settings.BOOKING_SESSION_FILL_KEY] = True
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

        if request.session.get(settings.BOOKING_SESSION_KEY, None) is None:
            return HttpResponseBadRequest()

        if self.object.pk.bytes != bytes(request.session[settings.BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        return self.render_to_response(self.get_context_data())


class ChooseDeliveryOrdered(UpdateView):
    form_class = DeliveryMode
    model = Ordered
    template_name = "sale/ordered_fill_delivery.html"

    def get_object(self, queryset=None):
        return get_object(self, queryset)

    def get_success_url(self):
        return reverse("sale:fill", kwargs={"pk": self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.ordered_is_enable:
            return HttpResponseRedirect(reverse("sale:fill", self.object.pk))

        form = self.get_form()
        if form.is_valid():
            self.request.session[settings.BOOKING_SESSION_FILL_DELIVERY] = True
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

        if request.session.get(settings.BOOKING_SESSION_KEY, None) is None:
            return HttpResponseBadRequest()

        if self.object.pk.bytes != bytes(request.session[settings.BOOKING_SESSION_KEY]):
            return HttpResponseBadRequest()

        return self.render_to_response(self.get_context_data())


class BookingBasketView(BaseFormView):
    form_class = OrderedForm
    model = Ordered

    def get_queryset(self):
        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        if bool(basket):
            queryset = Product.enable_objects.annotate(
                **stock_sold()
            ).filter(
                stock__gt=0
            ).filter(
                slug__in=tuple(basket.keys())
            ).annotate(
                **price_annotation_format(basket)
            ).annotate(
                **post_price_annotation_format()
            )
        else:
            queryset = None

        return queryset

    def get_success_url(self):
        amount = get_amount(self.ordered, with_promo=False) * BACK_TWO_PLACES
        amount = amount.quantize(TWO_PLACES)

        if settings.DELIVERY_FREE_GT < amount:
            return reverse("sale:fill", kwargs={"pk": self.ordered.pk})

        return reverse("sale:delivery", kwargs={"pk": self.ordered.pk})

    def check_queryset(self):
        if self.product_list is None:
            return HttpResponseBadRequest()

        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})

        basket_set = {product_slug for product_slug in basket.keys()}
        product_bdd_set = {product.slug for product in self.product_list}

        diff = basket_set.difference(product_bdd_set)

        if len(diff) > 0:
            return HttpResponseBadRequest()

        return None

    def form_valid(self, form):
        if self.request.session.get(settings.BOOKING_SESSION_KEY, None) is not None:
            messages.warning(
                self.request,
                "Vous avez déjà une commande en attente, une nouvelle reservation n'est pas possible."
            )
            return JsonResponse({"reload": True})

        self.product_list = self.get_queryset()
        response = self.check_queryset()

        if response is not None:
            return response

        basket = self.request.session.get(settings.BASKET_SESSION_KEY, {})
        promo_session = self.request.session.get(
            settings.PROMO_SESSION_KEY, {})
        promo = get_promo(basket, promo_session.get("code_promo", None))

        aggregate = self.get_queryset().aggregate(
            **total_price_from_all_product(promo=promo))

        try:
            with transaction.atomic():
                if promo is not None:
                    dict_ = {
                        "promo": promo, "promo_value": promo.value, "promo_type": promo.type,
                        "price_exact_ttc_with_quantity_sum_promo": int(
                            aggregate["price_exact_ttc_with_quantity_promo__sum"] *
                            Decimal(100.)
                        ),
                        "price_exact_ht_with_quantity_sum_promo": int(
                            aggregate["price_exact_ht_with_quantity_promo__sum"] *
                            Decimal(100.)
                        ),
                    }
                else:
                    dict_ = {}

                self.ordered = Ordered.objects.create(
                    price_exact_ht_with_quantity_sum=int(
                        aggregate["price_exact_ht_with_quantity__sum"].quantize(settings.BACK_TWO_PLACES) *
                        Decimal(100.)
                    ),
                    price_exact_ttc_with_quantity_sum=int(
                        aggregate["price_exact_ttc_with_quantity__sum"].quantize(settings.BACK_TWO_PLACES) *
                        Decimal(100.)
                    ),
                    secrets=''.join(secrets.choice(string.ascii_lowercase)
                                    for _ in range(settings.ORDER_SECRET_LENGTH)),
                    **dict_
                )

                ordered_product = []
                for product in self.product_list:
                    if product.effective_basket_quantity != basket[product.slug]["quantity"]:
                        raise ValueError()

                    ordered_product.append(
                        OrderedProduct(
                            from_ordered=self.ordered,
                            to_product=product,
                            product_name=product.name,
                            effective_reduction=product.effective_reduction,
                            price_exact_ht=int(
                                product.price_exact_ht.quantize(
                                    settings.BACK_TWO_PLACES) * Decimal(100.)
                            ),
                            price_exact_ttc=int(
                                product.price_exact_ttc.quantize(
                                    settings.BACK_TWO_PLACES) * Decimal(100.)
                            ),
                            price_exact_ht_with_quantity=int(
                                product.price_exact_ht_with_quantity.quantize(settings.BACK_TWO_PLACES) *
                                Decimal(100.)
                            ),
                            price_exact_ttc_with_quantity=int(
                                product.price_exact_ttc_with_quantity.quantize(settings.BACK_TWO_PLACES) *
                                Decimal(100.)
                            ),
                            quantity=product.effective_basket_quantity
                        )
                    )

            del self.request.session[settings.BASKET_SESSION_KEY]
            self.request.session[settings.BOOKING_SESSION_KEY] = list(
                self.ordered.pk.bytes)
            try:
                del self.request.session[settings.PROMO_SESSION_KEY]
            except KeyError:
                pass
            self.request.session.modified = True

            OrderedProduct.objects.bulk_create(ordered_product)

        except ValueError:
            return HttpResponseBadRequest()
        except IntegrityError():
            return HttpResponseBadRequest()

        messages.success(
            self.request, 'Votre panier a été correctement réservé.'
        )
        return JsonResponse({"redirect": self.get_success_url()})

    def form_invalid(self, form):
        return JsonResponse({
            "form_book": render_to_string(
                "sale/book.html",
                self.get_context_data(),
                self.request
            )
        })

    def get(self, request, *args, **kwargs):
        if not self.request.is_ajax():
            raise Http404()

        return JsonResponse({
            "form_book": render_to_string(
                "sale/book.html",
                self.get_context_data(),
                request
            )
        })
