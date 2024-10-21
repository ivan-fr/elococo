from django.urls import path
from rest_framework import routers
import catalogue.views

urlpatterns = [
    path('', catalogue.views.IndexView.as_view(), name='catalogue_index'),
    path('<slug:slug_category>/', catalogue.views.IndexView.as_view(), name='catalogue_navigation_categories'),
    path('detail/<slug:slug_product>/', catalogue.views.ProductDetailView.as_view(), name='catalogue_product_detail'),
    path('capte/basket/', catalogue.views.BasketView.as_view(), name='catalogue_basket'),
    path('capte/basket/surface', catalogue.views.BasketSurfaceView.as_view(), name='catalogue_basket_surface'),
    path('capte/basket/promo', catalogue.views.PromoBasketView.as_view(), name='catalogue_basket_promo'),
]

router = routers.SimpleRouter()
