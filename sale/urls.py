from django.urls import path

import sale.views

urlpatterns = [
    path('booking/', sale.views.BookingBasketView.as_view(), name='booking'),
    path('<uuid:pk>/fill/', sale.views.FillInformationOrdered.as_view(), name='fill'),
    path('<uuid:pk>/fill/next', sale.views.FillAddressInformationOrdered.as_view(), name='fill_next'),
    path('<uuid:pk>/', sale.views.OrderedDetail.as_view(), name='detail'),
    path('payment-done/<uuid:pk>/<str:secrets_>', sale.views.PaymentDoneView.as_view(), name='paypal_return'),
    path('payment-cancelled/<uuid:pk>/', sale.views.payment_canceled, name='paypal_cancel'),
    path('retrieve/', sale.views.RetrieveOrderedDetail.as_view(), name='retrieve'),
    path('invoice/<uuid:pk>/<str:secrets_>', sale.views.InvoiceView.as_view(), name='invoice'),
]
