from django.core.management.base import BaseCommand
from cinemaapp.models import Session


class Command(BaseCommand):
    help = 'checking current sessions'

    def handle(self, *args, **options):
        sessions = Session.objects.all()
        if sessions:
            for session in sessions:
                session.check_status()
        self.stdout.write(self.style.SUCCESS('Verification was successful'))
