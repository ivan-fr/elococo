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


def prices_effective(obj):
    return "{:.2f} euros".format(obj.exact_price)


def prices_base(obj):
    return "{:.2f} euros".format(obj.base_price)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'dateUpdate', 'stock', reductions, prices_base,
                    prices_effective, categories, 'enable_sale', 'enable_comment')
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
