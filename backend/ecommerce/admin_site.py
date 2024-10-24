from django.contrib.admin import AdminSite
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.sites.models import Site
from django.contrib.sites.admin import SiteAdmin

class MyAdminSite(AdminSite):
    site_header = "Ecommerce Admin"
    site_title = "Ecommerce Portail"
    index_title = "Bienvenue sur Ecommerce Admin Portail"


admin_site = MyAdminSite()
admin_site.register(FlatPage, FlatPageAdmin)
admin_site.register(Site, SiteAdmin)
