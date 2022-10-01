from django.urls import path, include
from . import views
from rest_framework import routers

api = routers.DefaultRouter()
api.register('accounts', views.AccountViewSet, basename='account')
api.register('transfers', views.TransferViewSet, basename='transfer')

urlpatterns = [
	path('', include(api.urls)),
]