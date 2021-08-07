from catalogue.bdd_calculations import cast_annotate_to_float, data_from_all_product, filled_category, price_annotation_format
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import catalogue.models as catalogue_models
import catalogue.serializers as catalogue_serializers


class CatalogueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = catalogue_models.Product.enable_objects.prefetch_related(
        "productimage_set"
    )
    serializer_class = catalogue_serializers.ProductSerializer

    def list(self, request, *args, **kwargs):
        self.serializer_class = catalogue_serializers.CatalogueSerializer

        dict_data = filled_category(5, None, products_queryset=self.queryset)
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

        queryset = self.filter_queryset(self.get_queryset())

        dict_data["related_products"] = self.paginate_queryset(queryset)
        if dict_data["related_products"] is not None:
            serializer = self.get_serializer(dict_data)
            return self.get_paginated_response(serializer.data)

        dict_data["related_products"] = queryset
        serializer = self.get_serializer(dict_data["related_products"])
        return Response(serializer.data)
