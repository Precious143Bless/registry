# decorators.py
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import ParishOfficerEP

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

def officer_required(view_func):
    """
    Decorator for views that both admin and parish officers can access.
    This also attaches the officer's parish to the request for filtering.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Superusers have full access
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Check if user is a parish officer
        try:
            officer = ParishOfficerEP.objects.filter(email=request.user.email, is_active=True).first()
            if officer:
                # Attach the officer and their parish to the request
                request.parish_officer = officer
                request.user_parish = officer.parish
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You are not authorized to access this page.')
                return redirect('dashboard')
        except Exception as e:
            print(f"Officer authorization error: {e}")
            messages.error(request, 'You are not authorized to access this page.')
            return redirect('dashboard')
    
    return wrapper