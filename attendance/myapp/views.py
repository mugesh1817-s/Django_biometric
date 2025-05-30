from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import AttendanceSerializer
from .models import Attendance
from django.db.models import Q
from datetime import datetime
from django.utils.text import slugify
from django.db.models import Count, Min, Max
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from myapp.utils import sync_attendance
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def admin_auth(request):
    if request.method == 'POST':
        if 'name' in request.POST:  # Sign Up
            name = request.POST.get('name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            cpassword = request.POST.get('cpassword')

            if password != cpassword:
                messages.error(request, "Passwords do not match.")
                return redirect('admin_auth')

            if User.objects.filter(username=email).exists():
                messages.error(request, "Email is already registered. Please log in")
                return redirect('admin_auth')

            user = User.objects.create_user(
                username=email, email=email, password=password, first_name=name)
            user.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('admin_auth')

        else:  # Login
            email = request.POST.get('email')
            password = request.POST.get('password')

            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "Login successful.")
                return redirect('api_attendance_summary')  # change to your desired redirect
            else:
                messages.error(request, "Invalid email or password.")
                return redirect('admin_auth')

    return render(request, 'adminlogin.html')


@api_view(['GET'])
def api_attendance_list(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    filtered_records = Attendance.objects.select_related('employee').all()

    if start_date:
        filtered_records = filtered_records.filter(timestamp__date__gte=parse_date(start_date))
    if end_date:
        filtered_records = filtered_records.filter(timestamp__date__lte=parse_date(end_date))

    serializer = AttendanceSerializer(filtered_records, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def api_attendance_summary(request):
    sync_attendance()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search', '')

    queryset = Attendance.objects.all()

    if start_date and end_date:
        queryset = queryset.filter(timestamp__date__range=[start_date, end_date])

    if search:
        queryset = queryset.filter(employee__name__icontains=search)

    summary = queryset.values(
        'employee__name',
        'employee__user_id',
        'timestamp__date'
    ).annotate(
        first_punch=Min('timestamp'),
        last_punch=Max('timestamp'),
        in_count=Count('id', filter=Q(status='IN')),   # ✅ changed from punch_type to status
        out_count=Count('id', filter=Q(status='OUT'))  # ✅
    ).order_by('-timestamp__date') 

    for item in summary:
        punches = queryset.filter(
            employee__user_id=item['employee__user_id'],
            timestamp__date=item['timestamp__date']
        ).order_by('timestamp')
        item['punch_list'] = [p.timestamp.strftime("%H:%M:%S") for p in punches]
        item['slug_key'] = f"{item['employee__user_id']}_{item['timestamp__date']}"

    return render(request, 'attendancelist.html', {
        'daily_summary': summary,
        'start_date': start_date,
        'end_date': end_date,
        'search': search,
        
    })

@api_view(['GET'])
def api_export_attendance_excel(request):
    import openpyxl

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    records = Attendance.objects.select_related('employee').all()

    if start_date:
        parsed_start = parse_date(start_date)
        if parsed_start:
            records = records.filter(timestamp__date__gte=parsed_start)

    if end_date:
        parsed_end = parse_date(end_date)
        if parsed_end:
            records = records.filter(timestamp__date__lte=parsed_end)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Records"

    ws.append(["Employee Name", "User ID", "Status", "Timestamp"])

    for record in records.order_by('-timestamp'):
        ws.append([
            record.employee.name,
            record.employee.user_id,
            record.status,
            record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=attendance.xlsx'
    wb.save(response)
    return response

@api_view(['POST'])
def api_run_attendance_sync(request):
    try:
        sync_attendance()
        return Response({'message': '✅ Attendance synced successfully!'})
    except Exception as e:
        return Response({'message': f'❌ Sync failed: {str(e)}'}, status=500)
