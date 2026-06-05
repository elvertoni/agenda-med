from django.urls import path

from . import views

app_name = 'clinic_content'

urlpatterns = [
    # Prices
    path('prices/', views.PriceItemListView.as_view(), name='price_list'),
    path('prices/new/', views.PriceItemCreateView.as_view(), name='price_create'),
    path('prices/<int:pk>/edit/', views.PriceItemUpdateView.as_view(), name='price_update'),
    path('prices/<int:pk>/delete/', views.PriceItemDeleteView.as_view(), name='price_delete'),
    # Service protocols
    path(
        'service-protocols/',
        views.ServiceProtocolListView.as_view(),
        name='service_protocol_list',
    ),
    path(
        'service-protocols/new/',
        views.ServiceProtocolCreateView.as_view(),
        name='service_protocol_create',
    ),
    path(
        'service-protocols/<int:pk>/edit/',
        views.ServiceProtocolUpdateView.as_view(),
        name='service_protocol_update',
    ),
    path(
        'service-protocols/<int:pk>/delete/',
        views.ServiceProtocolDeleteView.as_view(),
        name='service_protocol_delete',
    ),
    # Exam protocols
    path('exam-protocols/', views.ExamProtocolListView.as_view(), name='exam_protocol_list'),
    path(
        'exam-protocols/new/',
        views.ExamProtocolCreateView.as_view(),
        name='exam_protocol_create',
    ),
    path(
        'exam-protocols/<int:pk>/edit/',
        views.ExamProtocolUpdateView.as_view(),
        name='exam_protocol_update',
    ),
    path(
        'exam-protocols/<int:pk>/delete/',
        views.ExamProtocolDeleteView.as_view(),
        name='exam_protocol_delete',
    ),
]


public_urlpatterns = [
    path('precos/', views.PublicPricesView.as_view(), name='public_prices'),
    path(
        'protocolos-de-atendimento/',
        views.PublicServiceProtocolsView.as_view(),
        name='public_service_protocols',
    ),
    path(
        'protocolos-de-exames/',
        views.PublicExamProtocolsView.as_view(),
        name='public_exam_protocols',
    ),
]
