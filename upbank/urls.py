from django.contrib import admin
from django.urls import path, include

from knox import views as knox_views

from upbank.knox_login import LoginView

urlpatterns = [
	path('admin/', admin.site.urls),
	path('api/', include('banking.urls')),
	path('api/auth/login', LoginView.as_view(), name='knox_login'),
	path('api/auth/logout', knox_views.LogoutView.as_view(), name='knox_logout'),
	path('api/auth/logoutall', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
]
