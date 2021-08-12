from catalogue.bdd_calculations import (
    cast_annotate_to_float, data_from_all_product, filled_category, price_annotation_format)
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
import catalogue.models as catalogue_models
import catalogue.serializers as catalogue_serializers


def list_catalogue(self, request, **kwargs):
    self.serializer_class = catalogue_serializers.CatalogueSerializer

    dict_data = filled_category(5, kwargs.get(
        'slug_category', None), products_queryset=self.queryset,
        dump=True, request=request)
    dict_data.update({"index": None})

    selected_category_root = dict_data.get("selected_category_root", None)

    if selected_category_root is not None:
        dict_data.update({"index": selected_category_root.slug})

    if dict_data.get("related_products", None) is not None:
        self.queryset = dict_data["related_products"]
        dict_data["related_products"] = None

    annotation_p = price_annotation_format()
    cast_annotate_to_float(annotation_p, "price_exact_ttc")

    self.queryset = self.queryset.annotate(**annotation_p)
    dict_data.update(self.queryset.aggregate(*data_from_all_product()))
    
    try:
        min_ttc_price = float(request.GET.get("min_ttc_price", None))
        max_ttc_price = float(request.GET.get("max_ttc_price", None))
        if min_ttc_price is not None \
                and max_ttc_price is not None:
            if min_ttc_price < dict_data['price_exact_ttc__min']:
                min_ttc_price = dict_data['price_exact_ttc__min']
            if max_ttc_price > dict_data['price_exact_ttc__max']:
                max_ttc_price = dict_data['price_exact_ttc__max']
                self.queryset = self.queryset.filter(
                    price_exact_ttc__range=(
                        min_ttc_price - 1e-2,
                        max_ttc_price + 1e-2
                    )
                )
    except ValueError:
        pass

    order = request.GET.get("order", None)

    if order is not None:
        order = order.lower()
        if order == "asc":
            self.ordering = "price_exact_ttc"
        elif order == "desc":
            self.ordering = "-price_exact_ttc"
        else:
            order = None

        dict_data.update({"order": order})
    else:
        dict_data.update({"order": order})

    if self.ordering is not None:
        self.queryset = self.queryset.order_by(self.ordering)

    queryset = self.filter_queryset(self.get_queryset())

    dict_data["related_products"] = self.paginate_queryset(queryset)
    if dict_data["related_products"] is not None:
        serializer = self.get_serializer(dict_data)
        return self.get_paginated_response(serializer.data)

    dict_data["related_products"] = queryset
    serializer = self.get_serializer(dict_data["related_products"])
    return Response(serializer.data)


class CatalogueViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = catalogue_models.Product.enable_objects.prefetch_related(
        "productimage_set", "categories"
    )
    serializer_class = catalogue_serializers.ProductSerializer
    ordering = None

    def list(self, request, *args, **kwargs):
        return list_catalogue(self, request, **kwargs)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    def partial_update(self, request, *args, **kwargs):
        self.queryset = self.queryset.annotate(
            **price_annotation_format()
        )
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=False,
            methods=['GET'],
            url_path=r'categories/(?P<slug_category>[-\w]+)')
    def list_category(self, request, *args, **kwargs):
        return list_catalogue(self, request, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.queryset = self.queryset.annotate(
            **price_annotation_format()
        )
        return super().retrieve(request, *args, **kwargs)
