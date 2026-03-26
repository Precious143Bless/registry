from datetime import date, timedelta
from .models import Notification, Pledge


def notifications_processor(request):
    """Context processor to add notifications to all templates"""
    if request.user.is_authenticated:
        # Get unread notifications
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]  # Limit to 10 most recent

        # Check for pledges due tomorrow
        tomorrow = date.today() + timedelta(days=1)
        due_pledges = Pledge.objects.filter(
            due_date=tomorrow,
            status__in=['unpaid', 'partial']
        )

        # Create notifications for due pledges if they don't exist
        for pledge in due_pledges:
            notification, created = Notification.objects.get_or_create(
                user=request.user,
                notification_type='pledge_due',
                related_pledge=pledge,
                defaults={
                    'title': f'Pledge Payment Due Tomorrow',
                    'message': f'Payment of ₱{pledge.balance:.2f} is due tomorrow for {pledge.description} by {pledge.member.full_name}',
                    'is_read': False
                }
            )

        # Check for overdue pledges (past due date)
        overdue_pledges = Pledge.objects.filter(
            due_date__lt=date.today(),
            status__in=['unpaid', 'partial']
        )

        # Create notifications for overdue pledges if they don't exist
        for pledge in overdue_pledges:
            notification, created = Notification.objects.get_or_create(
                user=request.user,
                notification_type='pledge_overdue',
                related_pledge=pledge,
                defaults={
                    'title': f'Pledge Payment Overdue',
                    'message': f'Payment of ₱{pledge.balance:.2f} is overdue for {pledge.description} by {pledge.member.full_name}',
                    'is_read': False
                }
            )

        return {
            'unread_notifications': unread_notifications,
            'notification_count': unread_notifications.count(),
        }
    return {
        'unread_notifications': [],
        'notification_count': 0,
    }