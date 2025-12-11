from django.urls import path
from . import views

app_name = 'catalog'
urlpatterns = [
    path('', views.index, name='index'),
    path('day/<int:year>/<int:month>/<int:day>/', views.DayView.as_view(), name='calendar-day'),
    path('book/',views.book_event,name='book'),
    path('eventplanner_list/', views.EventPlannerListView.as_view(), name='eventplanner_list'),
    path('eventplanner_detail/<int:pk>', views.EventPlannerDetailView.as_view(), name='eventplanner_detail'),
    path('eventplanner/<int:pk>/update/', views.EventPlannerUpdate.as_view(),name='eventplanner_update'),
    path('eventplanner/<int:pk>/delete/', views.EventPlannerDelete, name="eventplanner_delete"),
    path('event_list/', views.EventListView.as_view(), name='event_list'),
    path('event_detail/<uuid:pk>', views.EventDetailView.as_view(), name='event_detail'),
    path('event/<uuid:pk>/update/', views.EventUpdate.as_view(), name='event_update'),
    path('event/<uuid:pk>/delete/', views.event_delete, name='event_delete'),
    path('become_event_planner/', views.become_event_planner, name="become_event_planner"),
    path('events/<uuid:event_id>/rsvp/<str:status>/', views.rsvp_event, name='rsvp_event'),
    path('my-rsvps/', views.UserRSVPListView.as_view(), name='my_rsvps'),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("manage-dates/", views.manage_dates, name="manage_dates"),
    path("manage-dates/unblock/<int:pk>", views.unblock_date, name="unblock_date"),
    path('events/<uuid:event_id>/notify/', views.create_event_notification, name='event_notification_create'),
    path('events/<uuid:event_id>/notify/send-now/', views.send_event_notification_now, name='event_notification_send_now'),
    path("manage-rooms/", views.manage_rooms, name="manage_rooms"),
    path("manage-rooms/new/", views.room_create, name="room_create"),
    path("manage-rooms/<uuid:pk>/edit/", views.room_edit, name="room_edit"),
    path("manage-rooms/<uuid:pk>/set-status/<str:status>/",
         views.room_set_status, name="room_set_status"),
]