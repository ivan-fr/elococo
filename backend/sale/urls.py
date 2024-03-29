from django.urls import path
from rest_framework import routers

import sale.views
from sale.rest_views import SaleBasketViewSet, SaleOrderViewSet

urlpatterns = [
    path('booking/', sale.views.BookingBasketView.as_view(), name='booking'),
    path('<uuid:pk>/delivery/', sale.views.ChooseDeliveryOrdered.as_view(), name="delivery"),
    path('<uuid:pk>/fill/', sale.views.FillInformationOrdered.as_view(), name='fill'),
    path('<uuid:pk>/fill/next', sale.views.FillAddressInformationOrdered.as_view(), name='fill_next'),
    path('<uuid:pk>/', sale.views.OrderedDetail.as_view(), name='detail'),
    path('payment-done/<uuid:pk>/<str:secrets_>', sale.views.PaymentDoneView.as_view(), name='payment_return'),
    path('payment-cancelled/<uuid:pk>/', sale.views.payment_canceled, name='payment_cancel'),
    path('retrieve/', sale.views.RetrieveOrderedDetail.as_view(), name='retrieve'),
    path('invoice/<uuid:pk>/<str:secrets_>', sale.views.InvoiceView.as_view(), name='invoice'),
    path('webhook', sale.views.webhook_view, name='webhook'),
]

router = routers.SimpleRouter()
router.register(r'sale/basket', SaleBasketViewSet)
router.register(r'sale/order', SaleOrderViewSet)
