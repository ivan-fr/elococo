from django.conf import settings
from rest_framework import serializers

import catalogue.models as catalogue_models
import sale.models as sale_models


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='catalogue_api:product-list-category',
        lookup_field='slug',
        lookup_url_kwarg='slug_category'
    )
    products_count__sum = serializers.IntegerField(default=None)
    path = serializers.CharField()

    @classmethod
    def MP_Node_dump_bulk_drf(cls, request, parent=None, annotates=None, depth_lte=None):
        """Dumps a tree branch to a python data structure."""

        # Because of fix_tree, this method assumes that the depth
        # and numchild properties in the nodes can be incorrect,
        # so no helper methods are used
        if annotates is None:
            annotates = {}
        qset = cls.Meta.model.objects.all()
        if parent:
            qset = qset.filter(path__startswith=parent.path,
                               depth__gte=parent.depth)

        if depth_lte is not None:
            qset = qset.filter(
                depth__lte=depth_lte
            )

        ret, lnk = [], {}

        if bool(annotates):
            qset = qset.annotate(**annotates)

        for obj in qset:
            newobj = {
                cls.Meta.model.__name__.lower(): cls(
                    obj, context={'request': request})
            }

            path = obj.path
            depth = int(len(path) / cls.Meta.model.steplen)

            if (not parent and depth == 1) or \
                    (parent and len(path) == len(parent.path)):
                ret.append(newobj)
            else:
                parentpath = cls.Meta.model._get_basepath(path, depth - 1)
                parentobj = lnk[parentpath]
                if 'children' not in parentobj:
                    parentobj['children'] = []
                parentobj['children'].append(newobj)
            lnk[path] = newobj
        return ret

    class Meta:
        model = catalogue_models.Category
        fields = ['url', 'category', 'slug', 'path', 'products_count__sum']

