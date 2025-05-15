from django.core.management.base import BaseCommand
from myapp.models import Attendance

class Command(BaseCommand):
    help = 'Display current attendance data'

    def handle(self, *args, **kwargs):
        for att in Attendance.objects.all().order_by('-timestamp')[:20]:
            self.stdout.write(f'{att.employee.name} - {att.timestamp} - {att.status}')
