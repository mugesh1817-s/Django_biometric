# myapp/management/commands/sync_attendance.py
from django.core.management.base import BaseCommand
from myapp.utils import sync_attendance  # Correct import

class Command(BaseCommand):
    help = 'Sync attendance manually from command'

    def handle(self, *args, **kwargs):
        count = sync_attendance()
        self.stdout.write(self.style.SUCCESS(f"✔️ Attendance synced! New records: {count}"))
