from rest_framework import serializers
from myapp.models import Attendance

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    user_id = serializers.CharField(source='employee.user_id', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'employee_name', 'user_id', 'status', 'timestamp']
