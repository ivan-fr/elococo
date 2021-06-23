from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from catalogue.bdd_calculations import price_annotation_format, annotate_effective_stock
from catalogue.models import Product, ProductImage, Category, ProductToProduct


@admin.register(Category)
class MyAdmin(TreeAdmin):
    prepopulated_fields = {"slug": ("category",)}
    form = movenodeform_factory(Category)


class ProductImageAdmin(admin.StackedInline):
    model = ProductImage
    extra = 0


def categories(obj):
    return "\n".join((category.category for category in obj.categories.all()))


def sub_products(obj):
    return "\n".join((productToProduct.elements.name for productToProduct in obj.box.all()))


def reductions(obj):
    if obj.effective_reduction == 0:
        return "No reduction"
    return "{}%".format(obj.effective_reduction)


def price_exact_ttc(obj):
    return "{:.2f} euros".format(obj.price_exact_ttc)


def price_exact_ht(obj):
    return "{:.2f} euros".format(obj.price_exact_ht)


def effective_stock(obj):
    return obj.effective_stock


def stock_sold(obj):
    return obj.stock_sold


class ElementProductToProduct(admin.TabularInline):
    model = ProductToProduct
    fk_name = "box"
    extra = 0

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(ElementProductToProduct, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'elements' and request.box_obj is not None:
            field.queryset = field.queryset.exclude(pk=request.box_obj.pk)

        return field


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'dateUpdate', 'stock', effective_stock, stock_sold, reductions, price_exact_ht,
                    price_exact_ttc, categories, sub_products, 'enable_sale', 'enable_comment')
    list_editable = ('enable_sale', 'enable_comment', "stock")
    filter_horizontal = ('categories',)
    inlines = (ElementProductToProduct, ProductImageAdmin)
    prepopulated_fields = {"slug": ("name",)}
    exclude = ('enable_sale',)
    change_form_template = "catalogue/admin/product_change_form.html"

    def get_form(self, request, obj=None, **kwargs):
        request.box_obj = obj
        return super(ProductAdmin, self).get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        queryset = super(ProductAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related(
            'box', 'box__elements', 'categories'
        ).annotate(
            **annotate_effective_stock(),
            **price_annotation_format()
        )
        return queryset

    class Meta:
        model = Product

    def get_list_display(self, request):
        return self.list_display

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return 'stock',
        else:
            return super(ProductAdmin, self).get_readonly_fields(request, obj)
