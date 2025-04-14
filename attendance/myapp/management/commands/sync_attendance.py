from django.core.management.base import BaseCommand
from zk import ZK
from django.utils import timezone
from myapp.models import Attendance, Employee  # Replace 'myapp' with your app name
from myapp.utils import sync_attendance

class Command(BaseCommand):
    help = 'Sync attendance logs from biometric device'

    def handle(self, *args, **kwargs):
        zk = ZK('192.168.1.20', port=4370, timeout=5)  # Update IP & port as needed

        try:
            conn = zk.connect()
            conn.disable_device()

            attendance_records = conn.get_attendance()
            count = 0  # Initialize counter

            for record in attendance_records:
                employee, _ = Employee.objects.get_or_create(
                    user_id=record.user_id,
                    defaults={'name': f"User {record.user_id}"}
                )

                obj, created = Attendance.objects.get_or_create(
                    employee=employee,
                    timestamp=timezone.make_aware(record.timestamp),
                    defaults={'status': 'IN'}
                )

                if created:
                    count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Synced: {employee.name} at {record.timestamp}"
                    ))
                else:
                    self.stdout.write(
                        f"ℹ️ Already exists: {employee.name} at {record.timestamp}"
                    )

            conn.enable_device()
            conn.disconnect()

            self.stdout.write(self.style.SUCCESS(f'✔️ Attendance sync complete. Total new records: {count}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))


# attendance/management/commands/sync_attendance.py

class Command(BaseCommand):
    help = 'Sync attendance manually'

    def handle(self, *args, **kwargs):
        sync_attendance()
        self.stdout.write(self.style.SUCCESS("Attendance synced successfully from command!"))
