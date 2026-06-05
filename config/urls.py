from django.contrib import admin
from django.urls import include, path

from clinic_content.urls import public_urlpatterns as content_public_urls
from core.landing import LandingView, PublicProfessionalsView
from core.portal import PortalHomeView
from core.views import DashboardView

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('profissionais/', PublicProfessionalsView.as_view(), name='public_professionals'),
    path('portal/', PortalHomeView.as_view(), name='portal_home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('messaging/', include('messaging.urls')),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('professionals/', include('professionals.urls')),
    path('scheduling/', include('scheduling.urls')),
    path('content/', include('clinic_content.urls')),
    path('', include((content_public_urls, 'clinic_content_public'))),
]
