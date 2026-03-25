from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard') if request.user.is_authenticated else redirect('landing')),
    path('', include('registry.urls')),
]