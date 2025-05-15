from django.db import models

class Employee(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=10, default='IN')

    def __str__(self):
        return f"{self.employee.name} - {self.timestamp}"
