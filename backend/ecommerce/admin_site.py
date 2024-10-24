from django.contrib.admin import AdminSite
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin


class MyAdminSite(AdminSite):
    site_header = "Ecommerce Admin"
    site_title = "Ecommerce Portail"
    index_title = "Bienvenue sur Ecommerce Admin Portail"


admin_site = MyAdminSite()
admin_site.register(FlatPage, FlatPageAdmin)
