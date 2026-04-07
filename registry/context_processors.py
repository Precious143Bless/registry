from datetime import date, timedelta
from .models import Notification, Pledge
from .models import ParishOfficerEP


def notifications_processor(request):
    """Context processor to add notifications to all templates"""
    if request.user.is_authenticated:
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Base pledge filter
        pledge_filter = {'status__in': ['unpaid', 'partial']}

        # If the logged-in user is a member, only show their own pledges
        if hasattr(request.user, 'member_profile'):
            pledge_filter['member'] = request.user.member_profile

        # Create notifications for pledges due today or tomorrow
        due_pledges = Pledge.objects.filter(
            due_date__in=[today, tomorrow],
            **pledge_filter
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
            **pledge_filter
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
    """Context processor to add parish priest information to all templates"""
    context = {
        'is_priest': False,
        'user_parish': None,
    }
    
    if request.user.is_authenticated:
        # Check if user is a parish priest
        if hasattr(request, 'user_parish') and request.user_parish:
            context['is_priest'] = True
            context['user_parish'] = request.user_parish
            print(f"Context processor: Using middleware parish: {request.user_parish.name}")
        elif not request.user.is_superuser:
            try:
                priest = ParishPriest.objects.filter(
                    email=request.user.email, 
                    status='active'
                ).first()
                if priest:
                    context['is_priest'] = True
                    context['user_parish'] = priest.parish
                    print(f"Context processor: Found parish {priest.parish.name} for priest {request.user.email}")
                else:
                    print(f"Context processor: No active priest found for {request.user.email}")
            except Exception as e:
                print(f"Context processor error: {e}")
    
    return context