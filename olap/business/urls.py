from django.urls import path
from . import views

urlpatterns = [
    path('', views.purchase_list, name='home'),
    path('chart/', views.purchase_chart, name='purchase_chart'),
    path('bycity/', views.sales_by_city, name='sales_by_city'), 
    path('avgpayment/', views.avg_payment_method, name='avg_payment_chart'), 
    path('shippingduration/', views.shipping_duration_chart, name='shipping_duration'),
    path('deliverydistribution/', views.delivery_distribution, name='delivery_distribution'),
]

