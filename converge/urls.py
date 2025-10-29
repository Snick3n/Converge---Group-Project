from django.contrib import admin
from django.urls import path, include
from django.urls import include
from catalog import views as catalog_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('catalog.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
