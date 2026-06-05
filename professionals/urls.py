from django.urls import path

from . import views

app_name = 'professionals'

urlpatterns = [
    path('', views.ProfessionalListView.as_view(), name='professional_list'),
    path('new/', views.ProfessionalCreateView.as_view(), name='professional_create'),
    path(
        '<int:pk>/edit/',
        views.ProfessionalUpdateView.as_view(),
        name='professional_update',
    ),
    path(
        '<int:pk>/delete/',
        views.ProfessionalDeleteView.as_view(),
        name='professional_delete',
    ),
    path('specialties/', views.SpecialtyListView.as_view(), name='specialty_list'),
    path('specialties/new/', views.SpecialtyCreateView.as_view(), name='specialty_create'),
    path(
        'specialties/<int:pk>/edit/',
        views.SpecialtyUpdateView.as_view(),
        name='specialty_update',
    ),
    path(
        'specialties/<int:pk>/delete/',
        views.SpecialtyDeleteView.as_view(),
        name='specialty_delete',
    ),
]
