"""ecommerce URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

import catalogue.views
from catalogue.urls import router as catalogue_router
from sale.urls import router as sale_router


def trigger_error(_):
    division_by_zero = 1 / 0


urlpatterns = [
    path('', catalogue.views.IndexView.as_view(), name='catalogue_index'),
    path('admin/', admin.site.urls),
    path('boutique/', include('catalogue.urls')),
    path('orders/', include(('sale.urls', 'sale'), namespace="sale")),
    path('api/', include((catalogue_router.urls, 'catalogue_api'), namespace="catalogue_api")),
    path('api/', include((sale_router.urls, 'sale_api'), namespace="sale_api")),
    path('accounts/', include('allauth.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [path('sentry-debug/', trigger_error)]
