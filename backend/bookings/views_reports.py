"""
Reports Intelligence API — Visual analytics endpoints
GET /api/reports/overview/
GET /api/reports/daily/
GET /api/reports/monthly/
GET /api/reports/staff/
GET /api/reports/insights/
GET /api/reports/staff-hours/
GET /api/reports/staff-hours/csv/
"""
import csv
from datetime import timedelta, date
from decimal import Decimal
from collections import defaultdict
from io import StringIO
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F, FloatField
from django.db.models.functions import TruncDate, TruncMonth, ExtractHour, ExtractWeekDay
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Booking, Client, Service, Staff
from .models_availability import TimesheetEntry


def _parse_date(s, default=None):
    if not s:
        return default
    try:
        parts = s.split('-')
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return default


def _base_qs(request):
    """Build base booking queryset from request filters."""
    now = timezone.now()
    date_from = _parse_date(request.query_params.get('date_from'), (now - timedelta(days=30)).date())
    date_to = _parse_date(request.query_params.get('date_to'), now.date())

    tenant = getattr(request, 'tenant', None)
    qs = Booking.objects.filter(
        start_time__date__gte=date_from,
        start_time__date__lte=date_to,
    ).select_related('client', 'service', 'staff')
    if tenant:
        qs = qs.filter(tenant=tenant)

    staff_id = request.query_params.get('staff_id')
    if staff_id:
        qs = qs.filter(staff_id=staff_id)

    service_id = request.query_params.get('service_id')
    if service_id:
        qs = qs.filter(service_id=service_id)

    risk_level = request.query_params.get('risk_level')
    if risk_level:
        qs = qs.filter(risk_level=risk_level)

    payment_status = request.query_params.get('payment_status')
    if payment_status:
        qs = qs.filter(payment_status=payment_status)

    return qs, date_from, date_to


@api_view(['GET'])
@permission_classes([AllowAny])
def reports_overview(request):
    """GET /api/reports/overview/ — KPI summary + revenue time series + risk distribution + service breakdown"""
    qs, date_from, date_to = _base_qs(request)

    total = qs.count()
    completed = qs.filter(status__in=['completed', 'confirmed']).count()
    no_shows = qs.filter(status='no_show').count()
    cancelled = qs.filter(status='cancelled').count()
    ns_rate = round(no_shows / total * 100, 1) if total > 0 else 0

    revenue = float(qs.filter(status__in=['completed', 'confirmed']).aggregate(
        t=Sum('service__price'))['t'] or 0)
    revenue_at_risk = float(qs.filter(
        risk_level__in=['HIGH', 'CRITICAL'],
        status__in=['confirmed', 'pending']
    ).aggregate(t=Sum('revenue_at_risk'))['t'] or 0)

    deposits = float(qs.filter(payment_status='paid').aggregate(
        t=Sum('payment_amount'))['t'] or 0)

    # Average reliability + risk
    client_ids = list(qs.values_list('client_id', flat=True).distinct())
    clients = Client.objects.filter(id__in=client_ids)
    avg_reliability = float(clients.aggregate(a=Avg('reliability_score'))['a'] or 0)
    avg_risk = float(qs.exclude(risk_score__isnull=True).aggregate(a=Avg('risk_score'))['a'] or 0)

    # Repeat client %
    client_booking_counts = qs.values('client_id').annotate(cnt=Count('id'))
    repeat_clients = client_booking_counts.filter(cnt__gte=2).count()
    unique_clients = client_booking_counts.count()
    repeat_pct = round(repeat_clients / unique_clients * 100, 1) if unique_clients > 0 else 0

    # Revenue time series (daily)
    rev_series = list(
        qs.filter(status__in=['completed', 'confirmed'])
        .annotate(day=TruncDate('start_time'))
        .values('day')
        .annotate(revenue=Sum('service__price'), count=Count('id'))
        .order_by('day')
    )
    revenue_timeline = [{'date': r['day'].isoformat(), 'revenue': float(r['revenue'] or 0), 'count': r['count']} for r in rev_series]

    # Revenue at risk time series
    risk_series = list(
        qs.filter(risk_level__in=['HIGH', 'CRITICAL'], status__in=['confirmed', 'pending'])
        .annotate(day=TruncDate('start_time'))
        .values('day')
        .annotate(at_risk=Sum('revenue_at_risk'))
        .order_by('day')
    )
    risk_timeline = [{'date': r['day'].isoformat(), 'at_risk': float(r['at_risk'] or 0)} for r in risk_series]

    # Risk distribution
    risk_dist = list(
        qs.exclude(risk_level__isnull=True).exclude(risk_level='')
        .values('risk_level')
        .annotate(count=Count('id'), revenue=Sum('service__price'))
        .order_by('risk_level')
    )
    risk_distribution = [{'level': r['risk_level'], 'count': r['count'], 'revenue': float(r['revenue'] or 0)} for r in risk_dist]

    # Service breakdown
    svc_breakdown = list(
        qs.filter(status__in=['completed', 'confirmed'])
        .values('service__id', 'service__name')
        .annotate(
            revenue=Sum('service__price'),
            volume=Count('id'),
            no_shows=Count('id', filter=Q(status='no_show')),
            risk_exposure=Sum('revenue_at_risk'),
        )
        .order_by('-revenue')
    )
    service_breakdown = [{
        'id': s['service__id'], 'name': s['service__name'],
        'revenue': float(s['revenue'] or 0), 'volume': s['volume'],
        'no_shows': s['no_shows'], 'risk_exposure': float(s['risk_exposure'] or 0),
    } for s in svc_breakdown]

    # Demand heatmap (hour x day_of_week)
    heatmap_data = list(
        qs.annotate(
            hour=ExtractHour('start_time'),
            dow=ExtractWeekDay('start_time'),
        )
        .values('hour', 'dow')
        .annotate(count=Count('id'))
        .order_by('dow', 'hour')
    )
    demand_heatmap = [{'hour': h['hour'], 'dow': h['dow'], 'count': h['count']} for h in heatmap_data]

    return Response({
        'kpi': {
            'revenue': revenue,
            'revenue_at_risk': revenue_at_risk,
            'deposits': deposits,
            'total_bookings': total,
            'completed': completed,
            'no_shows': no_shows,
            'cancelled': cancelled,
            'no_show_rate': ns_rate,
            'avg_reliability': round(avg_reliability, 1),
            'avg_risk_score': round(avg_risk, 1),
            'repeat_client_pct': repeat_pct,
            'unique_clients': unique_clients,
        },
        'revenue_timeline': revenue_timeline,
        'risk_timeline': risk_timeline,
        'risk_distribution': risk_distribution,
        'service_breakdown': service_breakdown,
        'demand_heatmap': demand_heatmap,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def reports_daily(request):
    """GET /api/reports/daily/ — Daily takings with no-show overlay"""
    qs, date_from, date_to = _base_qs(request)

    rows = list(
        qs.annotate(day=TruncDate('start_time'))
        .values('day')
        .annotate(
            revenue=Sum('service__price', filter=Q(status__in=['completed', 'confirmed'])),
            deposits=Sum('payment_amount', filter=Q(payment_status='paid')),
            at_risk=Sum('revenue_at_risk', filter=Q(risk_level__in=['HIGH', 'CRITICAL'])),
            bookings=Count('id', filter=Q(status__in=['completed', 'confirmed'])),
            no_shows=Count('id', filter=Q(status='no_show')),
            cancelled=Count('id', filter=Q(status='cancelled')),
            total=Count('id'),
        )
        .order_by('day')
    )

    return Response({
        'rows': [{
            'date': r['day'].isoformat(),
            'revenue': float(r['revenue'] or 0),
            'deposits': float(r['deposits'] or 0),
            'at_risk': float(r['at_risk'] or 0),
            'bookings': r['bookings'],
            'no_shows': r['no_shows'],
            'cancelled': r['cancelled'],
            'total': r['total'],
        } for r in rows],
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def reports_monthly(request):
    """GET /api/reports/monthly/ — Monthly aggregation with MoM growth"""
    qs, date_from, date_to = _base_qs(request)

    rows = list(
        qs.annotate(month=TruncMonth('start_time'))
        .values('month')
        .annotate(
            revenue=Sum('service__price', filter=Q(status__in=['completed', 'confirmed'])),
            deposits=Sum('payment_amount', filter=Q(payment_status='paid')),
            at_risk=Sum('revenue_at_risk', filter=Q(risk_level__in=['HIGH', 'CRITICAL'])),
            bookings=Count('id', filter=Q(status__in=['completed', 'confirmed'])),
            no_shows=Count('id', filter=Q(status='no_show')),
            total=Count('id'),
            avg_reliability=Avg('client__reliability_score'),
            avg_risk=Avg('risk_score'),
        )
        .order_by('month')
    )

    result = []
    prev_rev = None
    for r in rows:
        rev = float(r['revenue'] or 0)
        growth = None
        if prev_rev is not None and prev_rev > 0:
            growth = round((rev - prev_rev) / prev_rev * 100, 1)
        result.append({
            'month': r['month'].strftime('%Y-%m'),
            'revenue': rev,
            'deposits': float(r['deposits'] or 0),
            'at_risk': float(r['at_risk'] or 0),
            'bookings': r['bookings'],
            'no_shows': r['no_shows'],
            'total': r['total'],
            'avg_reliability': round(float(r['avg_reliability'] or 0), 1),
            'avg_risk': round(float(r['avg_risk'] or 0), 1),
            'mom_growth': growth,
        })
        prev_rev = rev

    return Response({'rows': result})


@api_view(['GET'])
@permission_classes([AllowAny])
def reports_staff(request):
    """GET /api/reports/staff/ — Per-staff performance"""
    qs, date_from, date_to = _base_qs(request)

    rows = list(
        qs.filter(staff__isnull=False)
        .values('staff__id', 'staff__name')
        .annotate(
            revenue=Sum('service__price', filter=Q(status__in=['completed', 'confirmed'])),
            bookings=Count('id', filter=Q(status__in=['completed', 'confirmed'])),
            no_shows=Count('id', filter=Q(status='no_show')),
            total=Count('id'),
            avg_reliability=Avg('client__reliability_score'),
            avg_risk=Avg('risk_score'),
            at_risk=Sum('revenue_at_risk', filter=Q(risk_level__in=['HIGH', 'CRITICAL'])),
        )
        .order_by('-revenue')
    )

    result = []
    for r in rows:
        total = r['total'] or 0
        ns = r['no_shows'] or 0
        ns_rate = round(ns / total * 100, 1) if total > 0 else 0
        result.append({
            'staff_id': r['staff__id'],
            'staff_name': r['staff__name'],
            'revenue': float(r['revenue'] or 0),
            'bookings': r['bookings'],
            'no_shows': ns,
            'total': total,
            'no_show_rate': ns_rate,
            'avg_reliability': round(float(r['avg_reliability'] or 0), 1),
            'avg_risk': round(float(r['avg_risk'] or 0), 1),
            'at_risk': float(r['at_risk'] or 0),
        })

    return Response({'rows': result})


@api_view(['GET'])
@permission_classes([AllowAny])
def reports_insights(request):
    """GET /api/reports/insights/ — AI-generated smart insights + recommended actions"""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)

    recent = Booking.objects.filter(start_time__gte=thirty_days_ago).select_related('client', 'service', 'staff')
    insights = []
    actions = []

    # 1. Day-of-week performance analysis
    dow_data = list(
        recent.filter(status__in=['completed', 'confirmed'])
        .annotate(dow=ExtractWeekDay('start_time'))
        .values('dow')
        .annotate(revenue=Sum('service__price'), count=Count('id'))
        .order_by('dow')
    )
    if len(dow_data) >= 3:
        avg_rev = sum(float(d['revenue'] or 0) for d in dow_data) / len(dow_data)
        dow_names = {1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday', 5: 'Thursday', 6: 'Friday', 7: 'Saturday'}
        for d in dow_data:
            rev = float(d['revenue'] or 0)
            if avg_rev > 0 and rev < avg_rev * 0.7:
                pct = round((1 - rev / avg_rev) * 100)
                day_name = dow_names.get(d['dow'], f"Day {d['dow']}")
                insights.append({
                    'type': 'warning',
                    'message': f'{day_name}s underperform by {pct}% vs average',
                    'metric': f'£{rev:.0f} vs £{avg_rev:.0f} avg',
                })
            elif avg_rev > 0 and rev > avg_rev * 1.3:
                pct = round((rev / avg_rev - 1) * 100)
                day_name = dow_names.get(d['dow'], f"Day {d['dow']}")
                insights.append({
                    'type': 'success',
                    'message': f'{day_name}s outperform by {pct}%',
                    'metric': f'£{rev:.0f} vs £{avg_rev:.0f} avg',
                })

    # 2. High risk client revenue exposure
    high_risk = recent.filter(risk_level__in=['HIGH', 'CRITICAL'], status__in=['confirmed', 'pending'])
    hr_revenue = float(high_risk.aggregate(t=Sum('revenue_at_risk'))['t'] or 0)
    hr_count = high_risk.count()
    if hr_count > 0:
        insights.append({
            'type': 'danger',
            'message': f'{hr_count} high-risk clients contribute £{hr_revenue:.0f} at risk',
            'metric': f'{hr_count} bookings',
        })

    # 3. Service no-show comparison
    svc_ns = list(
        recent.values('service__name')
        .annotate(
            total=Count('id'),
            ns=Count('id', filter=Q(status='no_show')),
        )
        .filter(total__gte=3)
        .order_by('-ns')
    )
    if len(svc_ns) >= 2:
        avg_ns_rate = sum(s['ns'] for s in svc_ns) / sum(s['total'] for s in svc_ns) * 100 if sum(s['total'] for s in svc_ns) > 0 else 0
        for s in svc_ns:
            rate = s['ns'] / s['total'] * 100 if s['total'] > 0 else 0
            if rate > avg_ns_rate * 1.5 and rate > 5:
                insights.append({
                    'type': 'warning',
                    'message': f'{s["service__name"]} has {rate:.0f}% no-show rate ({s["ns"]}/{s["total"]})',
                    'metric': f'{rate:.1f}% vs {avg_ns_rate:.1f}% avg',
                })

    # 4. Peak hour pricing opportunity
    peak_data = list(
        recent.filter(status__in=['completed', 'confirmed'])
        .annotate(hour=ExtractHour('start_time'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    if peak_data:
        top = peak_data[0]
        avg_count = sum(p['count'] for p in peak_data) / len(peak_data)
        if top['count'] > avg_count * 1.5:
            pct = round((top['count'] / avg_count - 1) * 100)
            insights.append({
                'type': 'info',
                'message': f'Peak demand at {top["hour"]:02d}:00 ({pct}% above average) — pricing increase opportunity',
                'metric': f'{top["count"]} bookings vs {avg_count:.0f} avg',
            })

    # 5. Repeat client loyalty
    repeat = recent.values('client_id').annotate(cnt=Count('id')).filter(cnt__gte=3)
    if repeat.count() > 0:
        insights.append({
            'type': 'success',
            'message': f'{repeat.count()} loyal clients with 3+ bookings this month',
            'metric': 'Consider loyalty incentive',
        })

    # --- Recommended Actions ---
    # Action 1: Services needing deposit increase
    for svc in Service.objects.filter(active=True):
        if svc.no_show_rate > 15 and svc.payment_type != 'full':
            potential = float(svc.total_revenue) * 0.1 if svc.total_revenue else 0
            actions.append({
                'severity': 'high',
                'action': f'Increase deposit for "{svc.name}" — {svc.no_show_rate:.0f}% no-show rate',
                'impact': f'+£{potential:.0f} protected revenue',
            })

    # Action 2: Off-peak discount opportunities
    for svc in Service.objects.filter(active=True, off_peak_utilisation_rate__lt=30, total_bookings__gt=0):
        actions.append({
            'severity': 'medium',
            'action': f'Consider off-peak discount for "{svc.name}" — only {svc.off_peak_utilisation_rate:.0f}% off-peak utilisation',
            'impact': 'Increase bookings in quiet periods',
        })

    # Action 3: Price increase candidates
    for svc in Service.objects.filter(active=True, peak_utilisation_rate__gt=80):
        increase = float(svc.price) * 0.1
        actions.append({
            'severity': 'medium',
            'action': f'Price increase opportunity for "{svc.name}" — {svc.peak_utilisation_rate:.0f}% peak utilisation',
            'impact': f'+£{increase:.0f} per booking potential',
        })

    # Action 4: Clients needing full payment
    risky_clients = Client.objects.filter(consecutive_no_shows__gte=2)
    for c in risky_clients[:3]:
        actions.append({
            'severity': 'high',
            'action': f'Require full payment for {c.name} — {c.consecutive_no_shows} consecutive no-shows',
            'impact': 'Reduce no-show risk',
        })

    return Response({
        'insights': insights[:8],
        'actions': actions[:6],
    })


# ════════════════════════════════════════════════════════════════
# Staff Hours — Monthly per-staff hours summary (real-time)
# ════════════════════════════════════════════════════════════════

def _staff_hours_data(request):
    """Build per-staff monthly hours data from TimesheetEntry records."""
    now = timezone.now()
    # Default: current month
    month_str = request.query_params.get('month')  # YYYY-MM
    if month_str:
        try:
            parts = month_str.split('-')
            year, month = int(parts[0]), int(parts[1])
            month_start = date(year, month, 1)
        except Exception:
            month_start = date(now.year, now.month, 1)
    else:
        month_start = date(now.year, now.month, 1)

    # Calculate month end
    if month_start.month == 12:
        month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)

    qs = TimesheetEntry.objects.filter(
        date__gte=month_start,
        date__lte=month_end,
    ).select_related('staff_member')

    # Exclude demo data
    include_demo = request.query_params.get('include_demo', '').lower() in ('1', 'true')
    if not include_demo:
        qs = qs.exclude(notes__contains='avail-demo')

    staff_filter = request.query_params.get('staff_id')
    if staff_filter:
        qs = qs.filter(staff_member_id=staff_filter)

    # Build per-staff summary
    staff_map = {}
    for entry in qs:
        sid = entry.staff_member_id
        if sid not in staff_map:
            staff_map[sid] = {
                'staff_id': sid,
                'staff_name': entry.staff_member.name,
                'scheduled_hours': 0,
                'actual_hours': 0,
                'days_worked': 0,
                'days_absent': 0,
                'overtime_hours': 0,
                'entries': [],
            }
        row = staff_map[sid]
        sh = entry.scheduled_hours or 0
        ah = entry.actual_hours or 0
        row['scheduled_hours'] += sh
        row['actual_hours'] += ah
        if ah > 0:
            row['days_worked'] += 1
        elif sh > 0 and ah == 0:
            row['days_absent'] += 1
        if ah > sh and sh > 0:
            row['overtime_hours'] += round(ah - sh, 2)
        row['entries'].append({
            'date': entry.date.isoformat(),
            'scheduled_hours': sh,
            'actual_hours': ah,
            'break_minutes': entry.break_minutes,
            'status': entry.status,
            'variance': entry.variance or 0,
        })

    rows = sorted(staff_map.values(), key=lambda r: r['staff_name'])
    for r in rows:
        r['scheduled_hours'] = round(r['scheduled_hours'], 2)
        r['actual_hours'] = round(r['actual_hours'], 2)
        r['overtime_hours'] = round(r['overtime_hours'], 2)
        r['variance_hours'] = round(r['actual_hours'] - r['scheduled_hours'], 2)

    # Totals
    total_scheduled = round(sum(r['scheduled_hours'] for r in rows), 2)
    total_actual = round(sum(r['actual_hours'] for r in rows), 2)
    total_overtime = round(sum(r['overtime_hours'] for r in rows), 2)

    return {
        'month': month_start.strftime('%Y-%m'),
        'month_start': month_start.isoformat(),
        'month_end': month_end.isoformat(),
        'totals': {
            'scheduled_hours': total_scheduled,
            'actual_hours': total_actual,
            'overtime_hours': total_overtime,
            'variance_hours': round(total_actual - total_scheduled, 2),
            'staff_count': len(rows),
        },
        'staff': rows,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def reports_staff_hours(request):
    """GET /api/reports/staff-hours/ — Monthly per-staff hours summary"""
    data = _staff_hours_data(request)
    # Strip daily entries from JSON response (keep it lightweight)
    for r in data['staff']:
        del r['entries']
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def reports_staff_hours_csv(request):
    """GET /api/reports/staff-hours/csv/ — Download monthly staff hours as CSV for payroll"""
    data = _staff_hours_data(request)
    month_label = data['month']

    output = StringIO()
    writer = csv.writer(output)

    # Summary mode (default) — one row per staff
    detail = request.query_params.get('detail', '').lower() in ('1', 'true')

    if detail:
        # Detailed: one row per staff per day
        writer.writerow([
            'Month', 'Staff Name', 'Date', 'Scheduled Hours',
            'Actual Hours', 'Break (min)', 'Overtime', 'Variance', 'Status',
        ])
        for staff_row in data['staff']:
            for entry in staff_row['entries']:
                sh = entry['scheduled_hours']
                ah = entry['actual_hours']
                ot = round(max(0, ah - sh), 2) if sh > 0 else 0
                writer.writerow([
                    month_label,
                    staff_row['staff_name'],
                    entry['date'],
                    f"{sh:.2f}",
                    f"{ah:.2f}",
                    entry['break_minutes'],
                    f"{ot:.2f}",
                    f"{entry['variance']:.2f}",
                    entry['status'],
                ])
    else:
        # Summary: one row per staff
        writer.writerow([
            'Month', 'Staff Name', 'Scheduled Hours', 'Actual Hours',
            'Overtime Hours', 'Variance Hours', 'Days Worked', 'Days Absent',
        ])
        for staff_row in data['staff']:
            writer.writerow([
                month_label,
                staff_row['staff_name'],
                f"{staff_row['scheduled_hours']:.2f}",
                f"{staff_row['actual_hours']:.2f}",
                f"{staff_row['overtime_hours']:.2f}",
                f"{staff_row['variance_hours']:.2f}",
                staff_row['days_worked'],
                staff_row['days_absent'],
            ])

        # Totals row
        writer.writerow([])
        writer.writerow([
            '', 'TOTAL',
            f"{data['totals']['scheduled_hours']:.2f}",
            f"{data['totals']['actual_hours']:.2f}",
            f"{data['totals']['overtime_hours']:.2f}",
            f"{data['totals']['variance_hours']:.2f}",
            '', '',
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="staff-hours-{month_label}.csv"'
    return response


# ════════════════════════════════════════════════════════════════
# Leave Report — Monthly leave summary
# ════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def reports_leave(request):
    """GET /api/reports/leave/ — Monthly leave summary with per-staff breakdown"""
    from .models_availability import LeaveRequest
    now = timezone.now()

    # Default: 12 months back
    months_back = int(request.query_params.get('months', '12'))
    start = date(now.year, now.month, 1) - timedelta(days=30 * months_back)

    qs = LeaveRequest.objects.filter(
        start_datetime__date__gte=start,
    ).exclude(reason__contains='avail-demo').select_related('staff_member')

    staff_filter = request.query_params.get('staff_id')
    if staff_filter:
        qs = qs.filter(staff_member_id=staff_filter)

    # Monthly aggregation
    from collections import defaultdict
    monthly = defaultdict(lambda: {'approved': 0, 'requested': 0, 'rejected': 0, 'cancelled': 0, 'total_days': 0})
    staff_summary = {}

    for lv in qs:
        month_key = lv.start_datetime.strftime('%Y-%m')
        days = max(1, (lv.end_datetime.date() - lv.start_datetime.date()).days)
        status_key = lv.status.lower()
        if status_key in monthly[month_key]:
            monthly[month_key][status_key] += 1
        if lv.status == 'APPROVED':
            monthly[month_key]['total_days'] += days

        sid = lv.staff_member_id
        if sid not in staff_summary:
            staff_summary[sid] = {
                'staff_id': sid,
                'staff_name': lv.staff_member.name,
                'approved_days': 0,
                'pending': 0,
                'total_requests': 0,
            }
        staff_summary[sid]['total_requests'] += 1
        if lv.status == 'APPROVED':
            staff_summary[sid]['approved_days'] += days
        elif lv.status == 'REQUESTED':
            staff_summary[sid]['pending'] += 1

    monthly_rows = [{'month': k, **v} for k, v in sorted(monthly.items())]
    staff_rows = sorted(staff_summary.values(), key=lambda r: r['staff_name'])

    total_approved_days = sum(r['approved_days'] for r in staff_rows)
    total_pending = sum(r['pending'] for r in staff_rows)

    return Response({
        'monthly': monthly_rows,
        'staff': staff_rows,
        'totals': {
            'approved_days': total_approved_days,
            'pending_requests': total_pending,
            'staff_count': len(staff_rows),
        },
    })
