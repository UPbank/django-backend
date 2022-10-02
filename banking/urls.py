from django.urls import path, include
from . import views
from rest_framework import routers

api = routers.DefaultRouter()
api.register('accounts', views.AccountView, basename='account')
api.register('transfers', views.TransferView, basename='transfer')
api.register('bank-transfers', views.BankTransferView, basename='bank-transfer')
api.register('service-payments', views.ServicePaymentView, basename='service-payment')
api.register('government-payments', views.GovernmentPaymentView, basename='government-payment')
api.register('telco-payments', views.TelcoPaymentView, basename='telco-payment')
api.register('telco-providers', views.TelcoProviderView, basename='telco-provider')
api.register('standing-orders', views.StandingOrderView, basename='standing-order')

urlpatterns = [
	path('', include(api.urls)),
]