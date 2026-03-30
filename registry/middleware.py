# middleware.py
from django.utils.deprecation import MiddlewareMixin
from .models import ParishOfficerEP


class ParishOfficerMiddleware(MiddlewareMixin):
    """
    Middleware to attach parish officer information to request
    """
    def process_request(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            try:
                officer = ParishOfficerEP.objects.filter(
                    email=request.user.email, 
                    is_active=True
                ).first()
                if officer:
                    request.parish_officer = officer
                    request.user_parish = officer.parish
                    print(f"Middleware: Attached parish '{officer.parish.name}' to user {request.user.email}")
                else:
                    print(f"Middleware: No active officer found for {request.user.email}")
            except Exception as e:
                print(f"Middleware error: {e}")