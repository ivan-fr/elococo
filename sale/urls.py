from django.urls import path

import sale.views

urlpatterns = [
    path('booking/', sale.views.BookingBasketView.as_view(), name='booking'),
    path('<int:pk>/fill/', sale.views.FillInformationOrdered.as_view(), name='fill'),
    path('<int:pk>/', sale.views.FillInformationOrdered.as_view(), name='detail'),
]
