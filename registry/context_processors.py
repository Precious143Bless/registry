# context_processors.py
from datetime import date, timedelta
from .models import Notification, Pledge
from .models import ParishOfficerEP


def notifications_processor(request):
    """Context processor to add notifications to all templates"""
    if request.user.is_authenticated:
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Create notifications for pledges due today or tomorrow
        due_pledges = Pledge.objects.filter(
            due_date__in=[today, tomorrow],
            status__in=['unpaid', 'partial']
        )
        for pledge in due_pledges:
            days_label = 'Today' if pledge.due_date == today else 'Tomorrow'
            Notification.objects.get_or_create(
                user=request.user,
                notification_type='pledge_due',
                related_pledge=pledge,
                is_read=False,
                defaults={
                    'title': f'Pledge Payment Due {days_label}',
                    'message': f'Payment of ₱{pledge.balance:.2f} is due {days_label.lower()} for {pledge.description} by {pledge.member.full_name}',
                }
            )

        # Create notifications for overdue pledges
        overdue_pledges = Pledge.objects.filter(
            due_date__lt=today,
            status__in=['unpaid', 'partial']
        )
        for pledge in overdue_pledges:
            Notification.objects.get_or_create(
                user=request.user,
                notification_type='pledge_overdue',
                related_pledge=pledge,
                is_read=False,
                defaults={
                    'title': 'Pledge Payment Overdue',
                    'message': f'Payment of ₱{pledge.balance:.2f} is overdue for {pledge.description} by {pledge.member.full_name}',
                }
            )

        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]

        return {
            'unread_notifications': unread_notifications,
            'notification_count': unread_notifications.count(),
        }
    return {
        'unread_notifications': [],
        'notification_count': 0,
    }


def parish_officer_context(request):
    """Context processor to add parish officer information to all templates"""
    context = {
        'is_officer': False,
        'user_parish': None,
    }
    
    if request.user.is_authenticated:
        # First check if middleware already attached the parish to the request
        if hasattr(request, 'user_parish') and request.user_parish:
            context['is_officer'] = True
            context['user_parish'] = request.user_parish
            print(f"Context processor: Using middleware parish: {request.user_parish.name}")
        # If not a superuser and middleware didn't attach, try to fetch from database
        elif not request.user.is_superuser:
            try:
                officer = ParishOfficerEP.objects.filter(
                    email=request.user.email, 
                    is_active=True
                ).first()
                if officer:
                    context['is_officer'] = True
                    context['user_parish'] = officer.parish
                    print(f"Context processor: Found parish {officer.parish.name} for {request.user.email}")
                else:
                    print(f"Context processor: No active officer found for {request.user.email}")
            except Exception as e:
                print(f"Context processor error: {e}")
    
    return context