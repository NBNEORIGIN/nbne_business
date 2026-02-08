from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db.models import Sum, Count
from accounts.permissions import IsManagerOrAbove
from .models import Recommendation
from .serializers import RecommendationSerializer


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def dashboard(request):
    """Cross-module analytics dashboard (manager+)."""
    data = {
        'bookings': _booking_stats(),
        'revenue': _revenue_stats(),
        'staff': _staff_stats(),
        'crm': _crm_stats(),
        'compliance': _compliance_stats(),
    }
    return Response(data)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def recommendations(request):
    """List active recommendations (manager+)."""
    recs = Recommendation.objects.filter(is_dismissed=False)
    return Response(RecommendationSerializer(recs, many=True).data)


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def dismiss_recommendation(request, rec_id):
    """Dismiss a recommendation (manager+)."""
    try:
        rec = Recommendation.objects.get(id=rec_id)
    except Recommendation.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    rec.is_dismissed = True
    rec.save(update_fields=['is_dismissed'])
    return Response({'dismissed': True})


@api_view(['POST'])
@permission_classes([IsManagerOrAbove])
def generate_recommendations(request):
    """Generate new recommendations based on current data (manager+)."""
    # Placeholder — in production this would run AI analysis
    generated = []
    booking_stats = _booking_stats()
    if booking_stats.get('cancelled', 0) > 2:
        rec, created = Recommendation.objects.get_or_create(
            title='High cancellation rate detected',
            defaults={
                'description': f"{booking_stats['cancelled']} bookings cancelled. Consider reviewing cancellation policy.",
                'recommendation_type': 'REVENUE', 'priority': 8,
            }
        )
        if created:
            generated.append(RecommendationSerializer(rec).data)

    compliance_stats = _compliance_stats()
    if compliance_stats.get('open_incidents', 0) > 0:
        rec, created = Recommendation.objects.get_or_create(
            title='Open compliance incidents require attention',
            defaults={
                'description': f"{compliance_stats['open_incidents']} open incidents. Review and resolve promptly.",
                'recommendation_type': 'COMPLIANCE', 'priority': 9,
            }
        )
        if created:
            generated.append(RecommendationSerializer(rec).data)

    return Response({'generated': len(generated), 'recommendations': generated})


def _booking_stats():
    try:
        from bookings.models import Booking
        qs = Booking.objects.all()
        return {
            'total': qs.count(),
            'confirmed': qs.filter(status='CONFIRMED').count(),
            'pending': qs.filter(status='PENDING').count(),
            'completed': qs.filter(status='COMPLETED').count(),
            'cancelled': qs.filter(status='CANCELLED').count(),
            'revenue_pence': qs.filter(status__in=['CONFIRMED', 'COMPLETED']).aggregate(t=Sum('price_pence'))['t'] or 0,
        }
    except Exception:
        return {}


def _revenue_stats():
    try:
        from bookings.models import Booking
        completed = Booking.objects.filter(status='COMPLETED')
        total = completed.aggregate(t=Sum('price_pence'))['t'] or 0
        count = completed.count()
        return {
            'total_pence': total,
            'average_pence': total // count if count > 0 else 0,
            'booking_count': count,
        }
    except Exception:
        return {}


def _staff_stats():
    try:
        from staff.models import StaffProfile, LeaveRequest, TrainingRecord
        return {
            'total': StaffProfile.objects.filter(is_active=True).count(),
            'pending_leave': LeaveRequest.objects.filter(status='PENDING').count(),
            'expired_training': sum(1 for t in TrainingRecord.objects.all() if t.is_expired),
        }
    except Exception:
        return {}


def _crm_stats():
    try:
        from crm.models import Lead
        qs = Lead.objects.all()
        return {
            'total_leads': qs.count(),
            'new': qs.filter(status='NEW').count(),
            'converted': qs.filter(status='CONVERTED').count(),
            'pipeline_pence': qs.exclude(status__in=['CONVERTED', 'LOST']).aggregate(t=Sum('value_pence'))['t'] or 0,
        }
    except Exception:
        return {}


def _compliance_stats():
    try:
        from compliance.models import IncidentReport, RAMSDocument
        return {
            'open_incidents': IncidentReport.objects.exclude(status__in=['RESOLVED', 'CLOSED']).count(),
            'total_incidents': IncidentReport.objects.count(),
            'active_rams': RAMSDocument.objects.filter(status='ACTIVE').count(),
        }
    except Exception:
        return {}
