"""elococo URL Configuration

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
from django.views.generic import TemplateView

import catalogue.views


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path('', catalogue.views.IndexView.as_view(), name='catalogue_index'),
    path('admin/', admin.site.urls),
    path('boutique/', include('catalogue.urls')),
    path('orders/', include(('sale.urls', 'sale'), namespace="sale")),
    path('ivan/cv', TemplateView.as_view(template_name="elococo/ivan_cv.html"), name="ivan_cv"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [path('sentry-debug/', trigger_error)]
