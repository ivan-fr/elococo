from django.urls import path

import sale.views

urlpatterns = [
    path('booking/', sale.views.BookingBasketView.as_view(), name='booking'),
    path('<uuid:pk>/fill/', sale.views.FillInformationOrdered.as_view(), name='fill'),
    path('<uuid:pk>/', sale.views.OrderedDetail.as_view(), name='detail'),
    path('payment-done/<uuid:pk>/', sale.views.payment_done, name='paypal_return'),
    path('payment-cancelled/<uuid:pk>/', sale.views.payment_canceled, name='paypal_cancel'),
]
