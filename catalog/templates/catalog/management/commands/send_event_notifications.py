from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from catalog.models import EventNotification, RSVP


class Command(BaseCommand):
    help = "Send scheduled event notification emails to attendees."

    def handle(self, *args, **options):
        now = timezone.now()
        notifications = EventNotification.objects.filter(sent=False, scheduled_for__lte=now)

        if not notifications.exists():
            self.stdout.write("No notifications to send.")
            return

        for notification in notifications:
            event = notification.event

            # Get all users who RSVP'd as attending
            rsvps = RSVP.objects.filter(event=event, status='y').select_related('user')
            recipients = [r.user.email for r in rsvps if r.user and r.user.email]

            if not recipients:
                self.stdout.write(
                    f"No recipients for notification {notification.id} ({event.name}); marking as sent."
                )
                notification.sent = True
                notification.save()
                continue

            subject = notification.subject
            body = notification.body

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )

            notification.sent = True
            notification.save()

            self.stdout.write(
                f"Sent notification {notification.id} for event '{event.name}' "
                f"to {len(recipients)} recipient(s)."
            )