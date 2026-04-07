from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import ParishOfficerEP, ParishPriest

def admin_required(view_func):
    """
    Decorator for views that only admin users can access.
    Admin users are superusers.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Superusers have full access
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Non-admin users get error message and redirect to dashboard
        messages.error(request, 'You do not have permission to access this page. Only administrators can access this section.')
        return redirect('dashboard')
    
    return wrapper

def priest_required(view_func):
    """
    Decorator for views that both admin and parish priests can access.
    Regular officers cannot access.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Superusers have full access
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Check if user is a parish priest (has a ParishPriest record)
        try:
            priest = ParishPriest.objects.filter(email=request.user.email, status='active').first()
            if priest:
                # Attach the priest and their parish to the request
                request.parish_priest = priest
                request.user_parish = priest.parish
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You are not authorized to access this page. Only parish priests can access this section.')
                return redirect('dashboard')
        except Exception as e:
            print(f"Priest authorization error: {e}")
            messages.error(request, 'You are not authorized to access this page.')
            return redirect('dashboard')
    
    return wrapper