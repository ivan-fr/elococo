from django.contrib import admin
from catalogue.models import Product, ProductImage, Category
from catalogue.bdd_calculations import price_annotation_format


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("category",)}

    class Meta:
        model = Category


class ProductImageAdmin(admin.StackedInline):
    model = ProductImage
    extra = 0


def categories(obj):
    return "\n".join((category.category for category in obj.categories.all()))


def reductions(obj):
    if obj.effective_reduction == 0:
        return "No reduction"
    return "{}%".format(obj.effective_reduction)


def price_exact_ttc(obj):
    return "{:.2f} euros".format(obj.price_exact_ttc)


def price_exact_ht(obj):
    return "{:.2f} euros".format(obj.price_exact_ht)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'dateUpdate', 'stock', reductions, price_exact_ht,
                    price_exact_ttc, categories, 'enable_sale', 'enable_comment')
    list_editable = ('enable_sale', 'enable_comment', 'stock')
    inlines = (ProductImageAdmin,)
    filter_horizontal = ('categories',)
    prepopulated_fields = {"slug": ("name",)}
    exclude = ('enable_sale',)
    change_form_template = "catalogue/admin/product_change_form.html"

    def get_queryset(self, request):
        queryset = super(ProductAdmin, self).get_queryset(request)
        queryset = queryset.annotate(**price_annotation_format())
        return queryset

    class Meta:
        model = Product
