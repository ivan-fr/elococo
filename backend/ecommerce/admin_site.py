from django.contrib.admin import AdminSite

class MyAdminSite(AdminSite):
    site_header = "Ecommerce Admin"
    site_title = "Ecommerce Portail"
    index_title = "Bienvenue sur Ecommerce Admin Portail"


admin_site = MyAdminSite()
