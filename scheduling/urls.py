from django.urls import path

from . import views

app_name = 'scheduling'

urlpatterns = [
    path(
        'availability/',
        views.AvailabilitySlotListView.as_view(),
        name='availability_slot_list',
    ),
    path(
        'availability/new/',
        views.AvailabilitySlotCreateView.as_view(),
        name='availability_slot_create',
    ),
    path(
        'availability/<int:pk>/edit/',
        views.AvailabilitySlotUpdateView.as_view(),
        name='availability_slot_update',
    ),
    path(
        'availability/<int:pk>/delete/',
        views.AvailabilitySlotDeleteView.as_view(),
        name='availability_slot_delete',
    ),
    path('appointments/', views.AppointmentListView.as_view(), name='appointment_list'),
    path(
        'appointments/new/',
        views.AppointmentCreateView.as_view(),
        name='appointment_create',
    ),
    path(
        'appointments/<int:pk>/edit/',
        views.AppointmentUpdateView.as_view(),
        name='appointment_update',
    ),
]
