import csv
from datetime import timedelta
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Lead, LeadNote, LeadHistory, LeadMessage


def _log_history(lead, action, detail=''):
    LeadHistory.objects.create(lead=lead, action=action, detail=detail)


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
        'marketing_consent': lead.marketing_consent,
        'client_id': lead.client_id,
        'action_required': lead.action_required,
        'client_score': lead.client_score,
        'client_score_label': lead.client_score_label,
        'sort_priority': lead.sort_priority,
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
    leads = [_serialize_lead(l) for l in qs]
    # Default sort: most important first
    leads.sort(key=lambda x: x['sort_priority'])
    return Response(leads)


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
        follow_up_date=d.get('follow_up_date') or None,
        marketing_consent=bool(d.get('marketing_consent', False)),
    )
    _log_history(lead, 'Lead created', f'Source: {lead.source}')
    return Response(_serialize_lead(lead), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_lead(request, lead_id):
    """Inline edit — accepts any subset of fields, logs changes to history."""
    try:
        tenant = getattr(request, 'tenant', None)
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    d = request.data
    changes = []

    if 'status' in d and d['status'] != lead.status:
        old = lead.status
        lead.status = d['status']
        changes.append(f'Status: {old} → {lead.status}')
    if 'name' in d and d['name'] != lead.name:
        lead.name = d['name']
        changes.append(f'Name updated')
    if 'email' in d and d['email'] != lead.email:
        lead.email = d['email']
        changes.append(f'Email updated')
    if 'phone' in d and d['phone'] != lead.phone:
        lead.phone = d['phone']
        changes.append(f'Phone updated')
    if 'value_pence' in d:
        val = int(d['value_pence'])
        if val != lead.value_pence:
            lead.value_pence = val
            changes.append(f'Value updated to £{val/100:.2f}')
    if 'source' in d and d['source'] != lead.source:
        lead.source = d['source']
        changes.append(f'Source updated')
    if 'notes' in d and d['notes'] != lead.notes:
        lead.notes = d['notes']
        changes.append(f'Notes updated')
    if 'tags' in d and d['tags'] != lead.tags:
        lead.tags = d['tags']
        changes.append(f'Tags updated')
    if 'follow_up_date' in d:
        new_val = d['follow_up_date'] or None
        if str(new_val) != str(lead.follow_up_date):
            lead.follow_up_date = new_val
            changes.append(f'Follow-up date set to {new_val or "none"}')
    if 'last_contact_date' in d:
        new_val = d['last_contact_date'] or None
        if str(new_val) != str(lead.last_contact_date):
            lead.last_contact_date = new_val
            changes.append(f'Last contact date updated')
    if 'marketing_consent' in d:
        val = bool(d['marketing_consent'])
        if val != lead.marketing_consent:
            lead.marketing_consent = val
            changes.append(f'Marketing consent {"given" if val else "withdrawn"}')

    lead.save()
    if changes:
        _log_history(lead, 'Updated', '; '.join(changes))
    return Response(_serialize_lead(lead))


@api_view(['POST'])
@permission_classes([AllowAny])
def action_contact(request, lead_id):
    """Owner clicks 'Contact now' — moves to CONTACTED, sets follow-up +7 days."""
    try:
        tenant = getattr(request, 'tenant', None)
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    today = timezone.now().date()
    lead.status = 'CONTACTED'
    lead.last_contact_date = today
    lead.follow_up_date = today + timedelta(days=7)
    lead.save()
    _log_history(lead, 'Contacted', f'Follow-up set for {lead.follow_up_date}')
    return Response(_serialize_lead(lead))


@api_view(['POST'])
@permission_classes([AllowAny])
def action_convert(request, lead_id):
    """Convert lead to client — creates bookings.Client if not already linked."""
    try:
        tenant = getattr(request, 'tenant', None)
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    lead.status = 'CONVERTED'
    lead.save()
    _log_history(lead, 'Converted to client')

    # Create bookings.Client if not already linked
    if not lead.client_id:
        try:
            from bookings.models import Client
            client, created = Client.objects.get_or_create(
                tenant=tenant, email=lead.email or f'lead-{lead.id}@placeholder.local',
                defaults={
                    'name': lead.name,
                    'phone': lead.phone,
                    'notes': f'Converted from CRM lead #{lead.id}',
                }
            )
            lead.client_id = client.id
            lead.save(update_fields=['client_id'])
            if created:
                _log_history(lead, 'Client record created', f'Client #{client.id}')
        except Exception:
            pass  # bookings app may not be available

    return Response(_serialize_lead(lead))


@api_view(['POST'])
@permission_classes([AllowAny])
def action_followup_done(request, lead_id):
    """Mark follow-up as done — reschedule +7 days."""
    try:
        tenant = getattr(request, 'tenant', None)
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    today = timezone.now().date()
    lead.last_contact_date = today
    lead.follow_up_date = today + timedelta(days=7)
    lead.save()
    _log_history(lead, 'Follow-up completed', f'Next follow-up: {lead.follow_up_date}')
    return Response(_serialize_lead(lead))


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_lead(request, lead_id):
    try:
        tenant = getattr(request, 'tenant', None)
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
    lead.delete()
    return Response({'deleted': True}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def quick_add(request):
    """Natural language quick-add: just name + optional notes."""
    tenant = getattr(request, 'tenant', None)
    text = request.data.get('text', '').strip()
    if not text:
        return Response({'error': 'Text required'}, status=status.HTTP_400_BAD_REQUEST)

    # Simple parse: first line = name, rest = notes
    parts = text.split('\n', 1)
    name = parts[0].strip()
    notes = parts[1].strip() if len(parts) > 1 else ''

    # If single line, try splitting on common delimiters
    if not notes and ' - ' in name:
        name, notes = name.split(' - ', 1)
    elif not notes and ': ' in name:
        # e.g. "Client John called wants quote" → name="John", notes="called wants quote"
        # But also "John: wants quote"
        if name.lower().startswith('client '):
            name = name[7:]
        # Try colon split
        if ': ' in name:
            name, notes = name.split(': ', 1)

    # Strip leading "client" if present
    if name.lower().startswith('client '):
        name = name[7:]

    lead = Lead.objects.create(
        tenant=tenant, name=name.strip(), notes=notes.strip(),
        source='manual', status='NEW',
    )
    _log_history(lead, 'Quick-added', f'From: "{text}"')
    return Response(_serialize_lead(lead), status=status.HTTP_201_CREATED)


# --- Notes ---

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def lead_notes(request, lead_id):
    try:
        tenant = getattr(request, 'tenant', None)
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        notes = lead.lead_notes.all()
        return Response([{
            'id': n.id, 'text': n.text, 'created_by': n.created_by,
            'created_at': n.created_at.isoformat(),
        } for n in notes])

    # POST
    text = request.data.get('text', '').strip()
    if not text:
        return Response({'error': 'Text required'}, status=status.HTTP_400_BAD_REQUEST)
    note = LeadNote.objects.create(
        lead=lead, text=text,
        created_by=request.data.get('created_by', ''),
    )
    _log_history(lead, 'Note added', text[:100])
    return Response({
        'id': note.id, 'text': note.text, 'created_by': note.created_by,
        'created_at': note.created_at.isoformat(),
    }, status=status.HTTP_201_CREATED)


# --- History ---

@api_view(['GET'])
@permission_classes([AllowAny])
def lead_history(request, lead_id):
    try:
        tenant = getattr(request, 'tenant', None)
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    history = lead.history.all()
    return Response([{
        'id': h.id, 'action': h.action, 'detail': h.detail,
        'created_at': h.created_at.isoformat(),
    } for h in history])


# --- CSV Export ---

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
    writer.writerow(['Name', 'Email', 'Phone', 'Value (£)', 'Status', 'Source', 'Consent', 'Follow Up', 'Notes', 'Created'])
    for lead in leads:
        writer.writerow([
            lead.name,
            lead.email,
            lead.phone,
            f'{lead.value_pence / 100:.2f}',
            lead.status,
            lead.source,
            'Yes' if lead.marketing_consent else 'No',
            lead.follow_up_date.isoformat() if lead.follow_up_date else '',
            lead.notes,
            lead.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


# --- Revenue Tracking ---

@api_view(['GET'])
@permission_classes([AllowAny])
def revenue_stats(request):
    """GET /api/crm/revenue/ — Pipeline forecast, source attribution, conversion funnel."""
    from collections import defaultdict
    from bookings.models import Client, Booking

    tenant = getattr(request, 'tenant', None)
    leads = Lead.objects.filter(tenant=tenant)

    # --- Per-lead revenue enrichment ---
    client_ids = [l.client_id for l in leads if l.client_id]
    clients_by_id = {}
    if client_ids:
        clients_by_id = {c.id: c for c in Client.objects.filter(id__in=client_ids, tenant=tenant)}

    # Booking aggregates per client
    booking_stats = {}
    if client_ids:
        from django.db.models import Sum, Count, Max, Q
        qs = Booking.objects.filter(
            client_id__in=client_ids, tenant=tenant
        ).values('client_id').annotate(
            total_bookings=Count('id'),
            completed_bookings=Count('id', filter=Q(status='completed')),
            total_revenue=Sum('payment_amount', filter=Q(status__in=['completed', 'confirmed'])),
            last_booking=Max('start_time'),
        )
        for row in qs:
            booking_stats[row['client_id']] = row

    # --- Pipeline forecast ---
    pipeline_value = 0
    converted_revenue = 0
    for l in leads:
        if l.status in ('NEW', 'CONTACTED', 'QUALIFIED'):
            pipeline_value += l.value_pence
        if l.status == 'CONVERTED' and l.client_id and l.client_id in booking_stats:
            rev = booking_stats[l.client_id].get('total_revenue') or 0
            converted_revenue += int(float(rev) * 100)  # Decimal → pence

    # --- Source attribution ---
    source_stats = defaultdict(lambda: {'leads': 0, 'converted': 0, 'revenue_pence': 0, 'pipeline_pence': 0})
    for l in leads:
        s = source_stats[l.source]
        s['leads'] += 1
        if l.status == 'CONVERTED':
            s['converted'] += 1
            if l.client_id and l.client_id in booking_stats:
                rev = booking_stats[l.client_id].get('total_revenue') or 0
                s['revenue_pence'] += int(float(rev) * 100)
        elif l.status != 'LOST':
            s['pipeline_pence'] += l.value_pence

    source_list = []
    for source, data in sorted(source_stats.items(), key=lambda x: -x[1]['revenue_pence']):
        conv_rate = (data['converted'] / data['leads'] * 100) if data['leads'] > 0 else 0
        source_list.append({
            'source': source,
            'leads': data['leads'],
            'converted': data['converted'],
            'conversion_rate': round(conv_rate, 1),
            'revenue_pence': data['revenue_pence'],
            'pipeline_pence': data['pipeline_pence'],
        })

    # --- Conversion funnel ---
    funnel = {}
    for s in ['NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST']:
        stage_leads = [l for l in leads if l.status == s]
        stage_value = sum(l.value_pence for l in stage_leads)
        funnel[s] = {'count': len(stage_leads), 'value_pence': stage_value}

    total_leads = leads.count()
    converted_count = funnel['CONVERTED']['count']
    overall_conversion_rate = round((converted_count / total_leads * 100) if total_leads > 0 else 0, 1)

    return Response({
        'pipeline_value_pence': pipeline_value,
        'converted_revenue_pence': converted_revenue,
        'total_leads': total_leads,
        'overall_conversion_rate': overall_conversion_rate,
        'sources': source_list,
        'funnel': funnel,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def lead_revenue(request, lead_id):
    """GET /api/crm/leads/<id>/revenue/ — Per-lead revenue: client stats + booking history."""
    from bookings.models import Client, Booking

    tenant = getattr(request, 'tenant', None)
    try:
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    if not lead.client_id:
        return Response({
            'linked': False,
            'message': 'No client record linked',
        })

    try:
        client = Client.objects.get(id=lead.client_id, tenant=tenant)
    except Client.DoesNotExist:
        return Response({'linked': False, 'message': 'Client record not found'})

    bookings = Booking.objects.filter(client=client, tenant=tenant).select_related('service').order_by('-start_time')

    booking_list = []
    for b in bookings[:20]:  # last 20 bookings
        booking_list.append({
            'id': b.id,
            'service': b.service.name if b.service else '—',
            'date': b.start_time.strftime('%Y-%m-%d'),
            'time': b.start_time.strftime('%H:%M'),
            'status': b.status,
            'amount_pence': int(float(b.payment_amount or 0) * 100) if b.payment_amount else (b.service.price_pence if b.service else 0),
        })

    return Response({
        'linked': True,
        'client_id': client.id,
        'client_name': client.name,
        'lifetime_value_pence': int(float(client.lifetime_value) * 100),
        'total_bookings': client.total_bookings,
        'completed_bookings': client.completed_bookings,
        'cancelled_bookings': client.cancelled_bookings,
        'no_show_count': client.no_show_count,
        'reliability_score': round(client.reliability_score, 1),
        'avg_days_between_bookings': client.avg_days_between_bookings,
        'bookings': booking_list,
    })


# --- Sync from bookings ---

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
            if Lead.objects.filter(tenant=tenant, client_id=client.id).exists():
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

            lead = Lead.objects.create(
                tenant=tenant,
                name=client.name,
                email=client.email,
                phone=client.phone,
                source='booking',
                status=lead_status,
                value_pence=total_pence,
                notes=f'Auto-imported from bookings. {bookings.count()} booking(s).',
                client_id=client.id,
            )
            _log_history(lead, 'Synced from bookings', f'{bookings.count()} booking(s), £{total_pence/100:.2f}')
            created_count += 1

        return Response({'created': created_count, 'message': f'{created_count} leads synced from bookings'})
    except Exception as e:
        return Response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)


# --- Lead Messages (Activity Feed) ---

def _serialize_message(msg):
    return {
        'id': msg.id,
        'message_type': msg.message_type,
        'subject': msg.subject,
        'body': msg.body,
        'created_by': msg.created_by,
        'ai_parsed': msg.ai_parsed,
        'created_at': msg.created_at.isoformat(),
    }


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def lead_messages(request, lead_id):
    tenant = getattr(request, 'tenant', None)
    try:
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        msgs = lead.messages.all()
        return Response([_serialize_message(m) for m in msgs])

    # POST — create a new message
    d = request.data
    msg = LeadMessage.objects.create(
        lead=lead,
        message_type=d.get('message_type', 'note'),
        subject=d.get('subject', ''),
        body=d.get('body', ''),
        created_by=d.get('created_by', ''),
    )
    _log_history(lead, f'{msg.get_message_type_display()} logged', msg.subject or msg.body[:80])
    return Response(_serialize_message(msg), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def parse_email(request, lead_id):
    """AI-parse a pasted email and save as a message on an existing lead.
    Extracts contact info and updates the lead if fields are empty."""
    tenant = getattr(request, 'tenant', None)
    try:
        lead = Lead.objects.get(id=lead_id, tenant=tenant)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

    email_text = request.data.get('text', '').strip()
    if not email_text:
        return Response({'error': 'No email text provided'}, status=status.HTTP_400_BAD_REQUEST)

    parsed = _ai_parse_email(email_text)
    if not parsed:
        return Response({'error': 'AI parsing failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Update lead with any missing fields
    changed = []
    if parsed.get('email') and not lead.email:
        lead.email = parsed['email']
        changed.append('email')
    if parsed.get('phone') and not lead.phone:
        lead.phone = parsed['phone']
        changed.append('phone')
    if parsed.get('name') and not lead.name:
        lead.name = parsed['name']
        changed.append('name')
    if changed:
        lead.save()
        _log_history(lead, 'AI updated fields', ', '.join(changed))

    # Save as message
    msg = LeadMessage.objects.create(
        lead=lead,
        message_type='email_in',
        subject=parsed.get('subject', ''),
        body=email_text,
        ai_parsed=parsed,
    )
    _log_history(lead, 'Email analyzed by AI', parsed.get('summary', '')[:100])

    return Response({
        'message': _serialize_message(msg),
        'parsed': parsed,
        'lead': _serialize_lead(lead),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def parse_email_create(request):
    """AI-parse a pasted email and create a NEW lead from it."""
    tenant = getattr(request, 'tenant', None)
    email_text = request.data.get('text', '').strip()
    if not email_text:
        return Response({'error': 'No email text provided'}, status=status.HTTP_400_BAD_REQUEST)

    parsed = _ai_parse_email(email_text)
    if not parsed:
        return Response({'error': 'AI parsing failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Create lead from parsed data
    value_pence = 0
    if parsed.get('estimated_value'):
        try:
            value_pence = int(float(str(parsed['estimated_value']).replace('£', '').replace(',', '')) * 100)
        except (ValueError, TypeError):
            pass

    lead = Lead.objects.create(
        tenant=tenant,
        name=parsed.get('name', 'Unknown'),
        email=parsed.get('email', ''),
        phone=parsed.get('phone', ''),
        source=parsed.get('source', 'website'),
        status='NEW',
        value_pence=value_pence,
        notes=parsed.get('summary', ''),
        tags=','.join(parsed.get('tags', [])),
    )
    _log_history(lead, 'Created from AI email analysis', parsed.get('summary', '')[:100])

    # Save original email as first message
    LeadMessage.objects.create(
        lead=lead,
        message_type='email_in',
        subject=parsed.get('subject', ''),
        body=email_text,
        ai_parsed=parsed,
    )

    return Response({
        'lead': _serialize_lead(lead),
        'parsed': parsed,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def parse_email_extract(request):
    """AI-parse a pasted email and return extracted data WITHOUT creating a lead.
    Used for the 'AI Extract Details' button in the Add Lead form."""
    email_text = request.data.get('text', '').strip()
    if not email_text:
        return Response({'error': 'No email text provided'}, status=status.HTTP_400_BAD_REQUEST)

    parsed = _ai_parse_email(email_text)
    if not parsed:
        return Response({'error': 'AI parsing failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'parsed': parsed})


def _ai_parse_email(email_text):
    """Call OpenAI to extract structured data from a pasted email/enquiry.
    Uses gpt-4o-mini with JSON response — typically ~300-500 tokens total."""
    import json
    import openai
    from django.conf import settings as django_settings

    api_key = getattr(django_settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return None

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{
                'role': 'system',
                'content': (
                    'You extract structured data from business enquiry emails. '
                    'Return JSON only. Be concise.'
                ),
            }, {
                'role': 'user',
                'content': (
                    'Extract the following from this email/enquiry:\n\n'
                    f'{email_text}\n\n'
                    'Return JSON with these fields:\n'
                    '{\n'
                    '  "name": "full name of the person",\n'
                    '  "email": "their email address or empty string",\n'
                    '  "phone": "their phone number or empty string",\n'
                    '  "subject": "brief subject line for this enquiry",\n'
                    '  "summary": "1-2 sentence summary of what they want",\n'
                    '  "enquiry_type": "one of: quote, booking, information, complaint, follow_up, other",\n'
                    '  "urgency": "one of: low, medium, high",\n'
                    '  "estimated_value": "estimated value in GBP if mentioned or inferable, or null",\n'
                    '  "source": "one of: website, referral, social, manual, other — infer from context",\n'
                    '  "tags": ["relevant", "tags", "as", "array"],\n'
                    '  "suggested_reply_points": ["key points to address in reply"]\n'
                    '}'
                ),
            }],
            response_format={'type': 'json_object'},
            temperature=0.2,
            max_tokens=500,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f'[CRM AI PARSE ERROR] {e}')
        return None
