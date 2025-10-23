from django.urls import path
from . import views

app_name = 'catalog'
urlpatterns = [
    path('', views.index, name='index'),
    path('day/<int:year>/<int:month>/<int:day>/', views.DayView.as_view(), name='calendar-day'),

]