from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from catalogue.bdd_calculations import price_annotation_format, stock_sold
from catalogue.models import Product, ProductImage, Category


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)


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


def stock_sold(obj):
    return obj.stock_sold


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'dateUpdate', 'stock', stock_sold, reductions, price_exact_ht,
                    price_exact_ttc, categories, 'enable_sale', 'enable_comment')
    list_editable = ('enable_sale', 'enable_comment', "stock")
    filter_horizontal = ('categories',)
    inlines = (ProductImageAdmin,)
    exclude = ('enable_sale', 'slug')
    change_form_template = "catalogue/admin/product_change_form.html"

    def get_queryset(self, request):
        queryset = super(ProductAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related(
            'categories'
        ).annotate(
            **stock_sold(),
            **price_annotation_format()
        )
        return queryset

    class Meta:
        model = Product
