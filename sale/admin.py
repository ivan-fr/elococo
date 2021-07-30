from django.conf import settings
from django.contrib import admin

from sale.forms import PromoForm
from sale.models import Ordered, Promo


def price_exact_ttc(obj):
    return "{:.2f} euros".format(obj.price_exact_ttc_with_quantity_sum * settings.BACK_TWO_PLACES)


def price_exact_ht(obj):
    return "{:.2f} euros".format(obj.price_exact_ht_with_quantity_sum * settings.BACK_TWO_PLACES)


@admin.register(Ordered)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', "createdAt", "endOfLife", "payment_status", 'email', 'phone', price_exact_ht,
                    price_exact_ttc, "delivery_mode")
    list_filter = ("payment_status",)

    change_form_template = "sale/admin/order_change_form.html"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(OrderAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related("order_address")
        return queryset

    class Meta:
        model = Ordered


@admin.register(Promo)
class MyAdmin(admin.ModelAdmin):
    form = PromoForm
