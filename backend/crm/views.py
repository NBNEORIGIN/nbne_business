import csv
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Lead


def _serialize_lead(lead):
    return {
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'phone': lead.phone,
        'source': lead.source,
        'status': lead.status,
        'value_pence': lead.value_pence,
        'notes': lead.notes,
        'tags': lead.tags,
        'follow_up_date': lead.follow_up_date.isoformat() if lead.follow_up_date else None,
        'last_contact_date': lead.last_contact_date.isoformat() if lead.last_contact_date else None,
        'client_id': lead.client_id,
        'created_at': lead.created_at.isoformat(),
        'updated_at': lead.updated_at.isoformat(),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def list_leads(request):
    tenant = getattr(request, 'tenant', None)
    qs = Lead.objects.filter(tenant=tenant)
    status_filter = request.query_params.get('status')
    if status_filter and status_filter != 'ALL':
        qs = qs.filter(status=status_filter)
    return Response([_serialize_lead(l) for l in qs])


@api_view(['POST'])
@permission_classes([AllowAny])
def create_lead(request):
    tenant = getattr(request, 'tenant', None)
    d = request.data
    lead = Lead.objects.create(
        tenant=tenant,
        name=d.get('name', ''),
        email=d.get('email', ''),
        phone=d.get('phone', ''),
        source=d.get('source', 'manual'),
        status=d.get('status', 'NEW'),
        value_pence=int(d.get('value_pence', 0)),
        notes=d.get('notes', ''),
    )
    return Response(_serialize_lead(lead), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_lead_status(request, lead_id):
    try:
        tenant = getattr(request, 'tenant', None)
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
    new_status = request.data.get('status')
    if new_status:
        lead.status = new_status
    # Also allow updating other fields
    if 'notes' in request.data:
        lead.notes = request.data['notes']
    if 'value_pence' in request.data:
        lead.value_pence = int(request.data['value_pence'])
    if 'source' in request.data:
        lead.source = request.data['source']
    if 'tags' in request.data:
        lead.tags = request.data['tags']
    if 'follow_up_date' in request.data:
        lead.follow_up_date = request.data['follow_up_date'] or None
    if 'last_contact_date' in request.data:
        lead.last_contact_date = request.data['last_contact_date'] or None
    if 'name' in request.data:
        lead.name = request.data['name']
    if 'email' in request.data:
        lead.email = request.data['email']
    if 'phone' in request.data:
        lead.phone = request.data['phone']
    lead.save()
    return Response(_serialize_lead(lead))


@api_view(['GET'])
@permission_classes([AllowAny])
def export_leads_csv(request):
    """GET /api/crm/leads/export/ — Download all leads as CSV"""
    tenant = getattr(request, 'tenant', None)
    leads = Lead.objects.filter(tenant=tenant)
    status_filter = request.query_params.get('status')
    if status_filter and status_filter != 'ALL':
        leads = leads.filter(status=status_filter)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="crm_leads_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Source', 'Status', 'Value (£)', 'Notes', 'Created'])
    for lead in leads:
        writer.writerow([
            lead.name,
            lead.email,
            lead.phone,
            lead.source,
            lead.status,
            f'{lead.value_pence / 100:.2f}',
            lead.notes,
            lead.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def sync_from_bookings(request):
    """POST /api/crm/sync/ — Create leads from booking clients that don't already exist"""
    import traceback
    try:
        from bookings.models import Client, Booking

        created_count = 0
        tenant = getattr(request, 'tenant', None)
        for client in Client.objects.filter(tenant=tenant):
            if Lead.objects.filter(client_id=client.id).exists():
                continue
            # Calculate total booking value for this client
            total_pence = 0
            bookings = Booking.objects.filter(client=client, status__in=['confirmed', 'completed'])
            for b in bookings:
                if b.service:
                    total_pence += b.service.price_pence

            lead_status = 'CONVERTED' if bookings.filter(status='completed').exists() else 'NEW'
            if bookings.filter(status='confirmed').exists() and lead_status == 'NEW':
                lead_status = 'QUALIFIED'

            Lead.objects.create(
                name=client.name,
                email=client.email,
                phone=client.phone,
                source='booking',
                status=lead_status,
                value_pence=total_pence,
                notes=f'Auto-imported from bookings. {bookings.count()} booking(s).',
                client_id=client.id,
            )
            created_count += 1

        return Response({'created': created_count, 'message': f'{created_count} leads synced from bookings'})
    except Exception as e:
        return Response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)
