from django.utils.deprecation import MiddlewareMixin
from .models import ParishOfficerEP


class ParishPriestMiddleware(MiddlewareMixin):
    """Middleware to attach parish priest information to request"""
    
    def process_request(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            try:
                priest = ParishPriest.objects.filter(
                    email=request.user.email, 
                    status='active'
                ).first()
                if priest:
                    request.parish_priest = priest
                    request.user_parish = priest.parish
                    print(f"Middleware: Attached parish '{priest.parish.name}' to priest {request.user.email}")
                else:
                    print(f"Middleware: No active priest found for {request.user.email}")
            except Exception as e:
                print(f"Middleware error: {e}")