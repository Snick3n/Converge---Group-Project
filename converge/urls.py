from django.contrib import admin
from django.urls import path, include
from catalog import views as catalog_views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalog.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('register.urls')),
]
