from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class StaffRequiredMixin(LoginRequiredMixin):
    '''Restrict a view to authenticated staff members.

    Anonymous users are redirected to the login URL (LoginRequiredMixin behavior).
    Authenticated non-staff users receive 403 instead of a redirect loop.
    '''

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PatientRequiredMixin(LoginRequiredMixin):
    '''Restrict a view to authenticated users that own a PatientProfile.

    Anonymous users are redirected to the login URL (LoginRequiredMixin behavior).
    Authenticated users without a related patient_profile receive 403, preventing
    staff members from leaking into the patient portal shell.
    '''

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not hasattr(request.user, 'patient_profile'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
