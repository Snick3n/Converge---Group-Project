from django.urls import path
from . import views


app_name = 'catalog'
urlpatterns = [
    path('', views.index, name='index'),
    path('day/<int:year>/<int:month>/<int:day>/', views.DayView.as_view(), name='calendar-day'),
    path('book/',views.book_event,name='book'),
    path('eventplanner_list/', views.EventPlannerListView.as_view(), name='eventplanner_list'),
    path('eventplanner_detail/<int:pk>', views.EventPlannerDetailView.as_view(), name='eventplanner_detail'),
    path('event_list/', views.EventListView.as_view(), name='event_list'),
    path('event_detail/<uuid:pk>', views.EventDetailView.as_view(), name='event_detail'),

]