from django.urls import path
from rest_framework.routers import DefaultRouter

import catalogue.views
from catalogue.api_views import ShopViewSet

router = DefaultRouter()
router.register(r'shop', ShopViewSet, basename='shop')
router.register(r'basket', ShopViewSet, basename='basket')

urlpatterns = [
    path('', catalogue.views.IndexView.as_view(), name='catalogue_index'),
    path('<slug:slug_category>/', catalogue.views.IndexView.as_view(), name='catalogue_navigation_categories'),
    path('detail/<slug:slug_product>/', catalogue.views.ProductDetailView.as_view(), name='catalogue_product_detail'),
    path('capte/basket/', catalogue.views.BasketView.as_view(), name='catalogue_basket'),
    path('capte/basket/promo', catalogue.views.PromoBasketView.as_view(), name='catalogue_basket_promo'),
]
