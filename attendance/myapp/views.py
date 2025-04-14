from django.utils.text import slugify
from django.shortcuts import render , redirect
import openpyxl
from django.http import HttpResponse
from .models import Attendance
from django.utils.dateparse import parse_date
from django.db.models import Count, Min, Max
from django.db.models import Q
from datetime import datetime
from django.http import HttpResponse
from django.http import JsonResponse



def run_attendance_sync(request):
    # Do your sync logic here (e.g., update DB)
    print("Attendance sync complete")
    return HttpResponse("Attendance sync complete")

def attendance_list(request):
    run_attendance_sync(request)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    filtered_records = Attendance.objects.select_related('employee')

    if start_date:
        filtered_records = filtered_records.filter(timestamp__date__gte=parse_date(start_date))
    if end_date:
        filtered_records = filtered_records.filter(timestamp__date__lte=parse_date(end_date))

    # Daily Summary
    daily_summary = filtered_records.values(
        'employee__name',
        'employee__user_id',
        'timestamp__date',
    ).annotate(
        first_punch=Min('timestamp'),
        last_punch=Max('timestamp'),
        in_count=Count('id', filter=Q(status='IN')),
        out_count=Count('id', filter=Q(status='OUT')),
    ).order_by('-timestamp__date', 'employee__name')

    # Punch map: key = slugified "user_id|date", value = list of timestamps
    punch_map = {}
    for record in filtered_records.order_by('timestamp'):
        raw_key = f"{record.employee.user_id}|{record.timestamp.date()}"
        key = slugify(raw_key)
        punch_map.setdefault(key, []).append(
            f"{record.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {record.status}"
        )

    # Add slug_key and punch_list to each summary item
    for item in daily_summary:
        raw_key = f"{item['employee__user_id']}|{item['timestamp__date']}"
        slug_key = slugify(raw_key)
        item['slug_key'] = slug_key
        item['punch_list'] = punch_map.get(slug_key, [])



    return render(request, 'attendancelist.html', {
        'daily_summary': daily_summary,
        'punch_map': punch_map,
        'start_date': start_date,
        'end_date': end_date,
    })



def attendance_summary_data(request):
    summary = Attendance.objects.values(
        'employee__name',
        'employee__user_id',
        'timestamp__date'
    ).annotate(
        first_punch=Min('timestamp'),
        last_punch=Max('timestamp'),
        in_count=Count('id', filter=Q(status='IN')),
        out_count=Count('id', filter=Q(status='OUT'))
    ).order_by('-timestamp__date')

    data = []
    for item in summary:
        data.append({
            'name': item['employee__name'],
            'user_id': item['employee__user_id'],
            'date': item['timestamp__date'],
            'first_punch': str(item['first_punch']),
            'last_punch': str(item['last_punch']),
            'in_count': item['in_count'],
            'out_count': item['out_count'],
        })

    return JsonResponse({'records': data})

def parse_date(date_str):
    """A function to safely parse dates."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def export_attendance_excel(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    records = Attendance.objects.select_related('employee').all()

    # Check if start_date is valid
    if start_date:
        parsed_start_date = parse_date(start_date)
        if parsed_start_date:
            records = records.filter(timestamp__date__gte=parsed_start_date)

    # Check if end_date is valid
    if end_date:
        parsed_end_date = parse_date(end_date)
        if parsed_end_date:
            records = records.filter(timestamp__date__lte=parsed_end_date)

    # Create the workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Records"

    # Write headers
    ws.append(["Employee Name", "User ID", "Status", "Timestamp"])

    # Write data rows
    for record in records.order_by('-timestamp'):
        ws.append([
            record.employee.name,
            record.employee.user_id,
            record.status,
            record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])

    # Return the response with the Excel file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=attendance.xlsx'
    wb.save(response)
    return response