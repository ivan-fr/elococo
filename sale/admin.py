from django.contrib import admin
from sale.models import Ordered

@admin.register(Ordered)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('order_number', "createdAt", "endOfLife", "payment_status", 'email', 'phone', "products", "price_exact_ht_with_quantity_sum",
                    "price_exact_ttc_with_quantity_sum")
    filter_horizontal = ('payment_status',)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        queryset = super(ProductAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related("order_address")
        return queryset

    class Meta:
        model = Ordered
