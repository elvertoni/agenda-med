from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    EmailLoginView,
    EmailPasswordResetCompleteView,
    EmailPasswordResetConfirmView,
    EmailPasswordResetDoneView,
    EmailPasswordResetView,
    UserRegistrationView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', EmailLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', UserRegistrationView.as_view(), name='signup'),
    path('password-reset/', EmailPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', EmailPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', EmailPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', EmailPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

