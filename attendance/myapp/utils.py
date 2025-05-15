from django.core.management.base import BaseCommand
from zk import ZK
from django.utils import timezone
from myapp.models import Attendance, Employee  # Replace 'myapp' with your app name



def sync_attendance():
    zk = ZK('192.168.1.201', port=4370, timeout=5)  # Update with your actual device IP & port

    try:
        conn = zk.connect()
        conn.disable_device()

        attendance_records = conn.get_attendance()
        count = 0

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
                print(f"✅ Synced: {employee.name} at {record.timestamp}")
            else:
                print(f"ℹ️ Already exists: {employee.name} at {record.timestamp}")

        conn.enable_device()
        conn.disconnect()

        print(f'✔️ Attendance sync complete. Total new records: {count}')
        return count

    except Exception as e:
        print(f'❌ Error during sync: {e}')
        return 0


# attendance/management/commands/sync_attendance.py



class Command(BaseCommand):
    help = 'Sync attendance manually'

    def handle(self, *args, **kwargs):
        count = sync_attendance()
        self.stdout.write(self.style.SUCCESS(f"Attendance synced successfully! New records: {count}"))
