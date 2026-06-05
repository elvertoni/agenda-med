from django.core.management.base import BaseCommand
from django.utils import timezone

from messaging.models import PresenceConfirmation
from messaging.services import send_due_presence_confirmations
from messaging.whatsapp import WhatsAppGateway


class Command(BaseCommand):
    help = 'Dispara confirmações de presença pendentes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Lista as confirmações pendentes sem enviar mensagens.',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options['dry_run']
        due_count = self._due_confirmations(now).count()

        self.stdout.write(f'pending_due={due_count}')

        if dry_run:
            self.stdout.write('dry_run=true')
            self.stdout.write('processed=0 sent=0 failed=0')
            return

        result = send_due_presence_confirmations(
            now=now,
            whatsapp_gateway=WhatsAppGateway(),
        )
        sent = result['sent']
        failed = result['failed']
        processed = sent + failed
        remaining_due = self._due_confirmations(now).count()

        self.stdout.write('dry_run=false')
        self.stdout.write(
            self.style.SUCCESS(
                (
                    f'processed={processed} sent={sent} '
                    f'failed={failed} remaining_due={remaining_due}'
                )
            )
        )

    def _due_confirmations(self, now):
        return PresenceConfirmation.objects.filter(
            status=PresenceConfirmation.Status.PENDING,
            scheduled_for__lte=now,
            appointment__status='scheduled',
        )
