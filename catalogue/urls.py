from django.urls import path
import catalogue.views

urlpatterns = [
    path('', catalogue.views.IndexView.as_view(), name='catalogue_index'),
    path('<slug:slug_category>/', catalogue.views.IndexView.as_view(), name='catalogue_navigation_categories'),
    path('detail/<slug:slug_product>/', catalogue.views.ProductDetailView.as_view(), name='catalogue_product_detail')
]
