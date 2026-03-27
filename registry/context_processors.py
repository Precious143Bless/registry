from datetime import date, timedelta
from .models import Notification, Pledge


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
