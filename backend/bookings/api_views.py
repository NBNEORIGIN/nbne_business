from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Service, Staff, Client, Booking, Session, StaffBlock, ServiceOptimisationLog
from .serializers import ServiceSerializer, StaffSerializer, ClientSerializer, BookingSerializer, SessionSerializer
from .utils import generate_time_slots, get_available_dates


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        # Admin sees all services; public booking page sees only active
        tenant = getattr(self.request, 'tenant', None)
        qs = Service.objects.filter(tenant=tenant) if tenant else Service.objects.none()
        show_all = self.request.query_params.get('all', '')
        if show_all == '1' or self.action in ('update', 'partial_update', 'destroy', 'retrieve'):
            return qs
        return qs.filter(active=True)

    def perform_create(self, serializer):
        # Support price_pence from frontend (convert to pounds)
        tenant = getattr(self.request, 'tenant', None)
        price_pence = self.request.data.get('price_pence')
        if price_pence is not None:
            serializer.save(price=int(price_pence) / 100, tenant=tenant)
        else:
            serializer.save(tenant=tenant)

    def perform_update(self, serializer):
        price_pence = self.request.data.get('price_pence')
        if price_pence is not None:
            serializer.save(price=int(price_pence) / 100)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response(
                {'error': 'Cannot delete this service because it has existing bookings. Disable it instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='assign-staff')
    def assign_staff(self, request, pk=None):
        """POST /api/services/<id>/assign-staff/ {staff_ids: [1,2,3]}"""
        service = self.get_object()
        staff_ids = request.data.get('staff_ids', [])
        service.staff_members.set(Staff.objects.filter(id__in=staff_ids))
        return Response(ServiceSerializer(service).data)

    @action(detail=True, methods=['get'], url_path='optimisation-logs')
    def optimisation_logs(self, request, pk=None):
        """GET /api/services/<id>/optimisation-logs/ — R&D audit trail"""
        service = self.get_object()
        logs = service.optimisation_logs.all()[:50]
        return Response([{
            'id': l.id,
            'previous_price': float(l.previous_price) if l.previous_price else None,
            'new_price': float(l.new_price) if l.new_price else None,
            'previous_deposit': l.previous_deposit,
            'new_deposit': l.new_deposit,
            'reason': l.reason,
            'ai_recommended': l.ai_recommended,
            'owner_override': l.owner_override,
            'input_metrics': l.input_metrics,
            'output_recommendation': l.output_recommendation,
            'timestamp': l.timestamp.isoformat(),
        } for l in logs])

    @action(detail=True, methods=['post'], url_path='apply-recommendation')
    def apply_recommendation(self, request, pk=None):
        """POST /api/services/<id>/apply-recommendation/ — Owner approves AI suggestion"""
        service = self.get_object()
        if not service.recommended_base_price and not service.recommended_deposit_percent:
            return Response({'error': 'No recommendation available'}, status=status.HTTP_400_BAD_REQUEST)

        prev_price = service.price
        prev_deposit = service.deposit_percentage or service.deposit_pence

        if service.recommended_base_price:
            service.price = service.recommended_base_price
        if service.recommended_deposit_percent:
            service.deposit_percentage = int(service.recommended_deposit_percent)
            service.deposit_pence = 0
        if service.recommended_payment_type:
            service.payment_type = service.recommended_payment_type
        service.save()

        ServiceOptimisationLog.objects.create(
            service=service,
            previous_price=prev_price,
            new_price=service.price,
            previous_deposit=prev_deposit,
            new_deposit=service.deposit_percentage,
            reason=f'Owner approved AI recommendation: {service.recommendation_reason}',
            ai_recommended=True,
            owner_override=False,
            input_metrics=service.recommendation_snapshot,
            output_recommendation={
                'applied_price': float(service.price),
                'applied_deposit': service.deposit_percentage,
                'applied_payment_type': service.payment_type,
            },
        )
        return Response(ServiceSerializer(service).data)

    @action(detail=True, methods=['post'], url_path='log-override')
    def log_override(self, request, pk=None):
        """POST /api/services/<id>/log-override/ — Log a manual price/deposit change"""
        service = self.get_object()
        ServiceOptimisationLog.objects.create(
            service=service,
            previous_price=request.data.get('previous_price'),
            new_price=request.data.get('new_price'),
            previous_deposit=request.data.get('previous_deposit'),
            new_deposit=request.data.get('new_deposit'),
            reason=request.data.get('reason', 'Manual owner override'),
            ai_recommended=False,
            owner_override=True,
        )
        return Response({'status': 'logged'})

    @action(detail=False, methods=['post'], url_path='recalculate-intelligence')
    def recalculate_intelligence(self, request):
        """POST /api/services/recalculate-intelligence/ — Trigger intelligence recalc"""
        from django.core.management import call_command
        import io
        out = io.StringIO()
        call_command('update_service_intelligence', stdout=out)
        return Response({'status': 'ok', 'message': out.getvalue().strip()})

    @action(detail=False, methods=['get'], url_path='optimisation-csv')
    def optimisation_csv(self, request):
        """GET /api/services/optimisation-csv/ — Export R&D audit trail as CSV"""
        import csv
        from django.http import HttpResponse
        logs = ServiceOptimisationLog.objects.select_related('service').all()[:500]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="service_optimisation_log.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Service', 'Previous Price', 'New Price', 'Previous Deposit',
                        'New Deposit', 'Reason', 'AI Recommended', 'Owner Override', 'Timestamp'])
        for l in logs:
            writer.writerow([l.id, l.service.name, l.previous_price, l.new_price,
                           l.previous_deposit, l.new_deposit, l.reason,
                           l.ai_recommended, l.owner_override, l.timestamp.isoformat()])
        return response


class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        qs = Staff.objects.filter(tenant=tenant) if tenant else Staff.objects.none()
        show_all = self.request.query_params.get('all', '')
        if show_all == '1' or self.action in ('update', 'partial_update', 'destroy', 'retrieve'):
            return qs
        qs = qs.filter(active=True)
        service_id = self.request.query_params.get('service_id')
        if service_id:
            qs = qs.filter(services__id=service_id).distinct()
        return qs

    def _get_name(self, data):
        """Extract name from first_name+last_name or name field."""
        if 'first_name' in data or 'last_name' in data:
            first = data.get('first_name', '').strip()
            last = data.get('last_name', '').strip()
            return f'{first} {last}'.strip()
        return data.get('name', '').strip() or None

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        name = self._get_name(self.request.data)
        if name:
            serializer.save(name=name, tenant=tenant)
        else:
            serializer.save(tenant=tenant)

    def perform_update(self, serializer):
        name = self._get_name(self.request.data)
        if name:
            serializer.save(name=name)
        else:
            serializer.save()


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        return Client.objects.filter(tenant=tenant) if tenant else Client.objects.none()

    def perform_create(self, serializer):
        serializer.save(tenant=getattr(self.request, 'tenant', None))


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        return Booking.objects.filter(tenant=tenant) if tenant else Booking.objects.none()
    
    def get_permissions(self):
        if self.action in ('create', 'slots', 'available_dates'):
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Create a booking. Accepts client details and creates/finds client automatically.
        Expected data: service, staff, date, time, client_name, client_email, client_phone, notes
        """
        from datetime import datetime
        from django.db import transaction
        
        # Extract data (accept both old and new field names)
        service_id = request.data.get('service') or request.data.get('service_id')
        staff_id = request.data.get('staff') or request.data.get('staff_id')
        date_str = request.data.get('date') or request.data.get('booking_date')
        time_str = request.data.get('time') or request.data.get('booking_time')
        client_name = request.data.get('client_name') or request.data.get('customer_name')
        client_email = request.data.get('client_email') or request.data.get('customer_email')
        client_phone = request.data.get('client_phone') or request.data.get('customer_phone')
        notes = request.data.get('notes', '')
        
        # Validate required fields
        if not all([service_id, staff_id, date_str, time_str, client_name, client_email, client_phone]):
            return Response(
                {'error': 'Missing required fields: service, staff, date, time, client_name, client_email, client_phone'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Find or create client by email (scoped to tenant)
                tenant = getattr(request, 'tenant', None)
                client, created = Client.objects.get_or_create(
                    tenant=tenant, email=client_email,
                    defaults={
                        'name': client_name,
                        'phone': client_phone,
                    }
                )
                
                # If client exists but name/phone changed, update them
                if not created:
                    if client.name != client_name or client.phone != client_phone:
                        client.name = client_name
                        client.phone = client_phone
                        client.save()
                
                # Get staff and service
                staff = Staff.objects.get(id=staff_id, active=True)
                service = Service.objects.get(id=service_id, active=True)
                
                # Parse date and time into datetime
                from django.utils import timezone as tz
                datetime_str = f"{date_str} {time_str}"
                start_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                start_datetime = tz.make_aware(start_datetime)
                
                # Calculate end time based on service duration
                from datetime import timedelta
                end_datetime = start_datetime + timedelta(minutes=service.duration_minutes)
                
                # Check for overlapping bookings with this staff member
                overlapping_bookings = Booking.objects.filter(
                    staff=staff,
                    status__in=['pending', 'confirmed'],
                    start_time__lt=end_datetime,
                    end_time__gt=start_datetime
                )
                
                if overlapping_bookings.exists():
                    return Response(
                        {'error': 'This time slot is no longer available. Please select a different time.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create booking
                booking = Booking.objects.create(
                    tenant=tenant,
                    client=client,
                    staff=staff,
                    service=service,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    status='confirmed',
                    notes=notes
                )
                
                # Smart Booking Engine — run full pipeline
                try:
                    from .smart_engine import process_booking
                    process_booking(booking)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f'[SBE] Engine error on booking {booking.id}: {e}')

                # Auto-create CRM lead if not exists
                try:
                    from crm.models import Lead
                    if not Lead.objects.filter(client_id=client.id).exists():
                        Lead.objects.create(
                            name=client.name,
                            email=client.email,
                            phone=client.phone,
                            source='booking',
                            status='QUALIFIED',
                            value_pence=service.price_pence,
                            notes=f'Auto-created from booking #{booking.id}',
                            client_id=client.id,
                        )
                except Exception:
                    pass  # CRM is optional, don't break bookings

                # Refresh from DB to get SBE-updated fields
                booking.refresh_from_db()

                # Prepare response data first
                response_data = {
                    'id': booking.id,
                    'client': booking.client.id,
                    'client_name': booking.client.name,
                    'service': booking.service.id,
                    'service_name': booking.service.name,
                    'staff': booking.staff.id,
                    'staff_name': booking.staff.name,
                    'start_time': booking.start_time.isoformat(),
                    'end_time': booking.end_time.isoformat(),
                    'status': booking.status,
                    'notes': booking.notes,
                    'risk_score': booking.risk_score,
                    'risk_level': booking.risk_level,
                    'revenue_at_risk': float(booking.revenue_at_risk) if booking.revenue_at_risk else None,
                    'recommended_payment_type': booking.recommended_payment_type,
                    'recommended_deposit_percent': booking.recommended_deposit_percent,
                    'recommended_price_adjustment': float(booking.recommended_price_adjustment) if booking.recommended_price_adjustment else None,
                    'recommended_incentive': booking.recommended_incentive,
                    'recommendation_reason': booking.recommendation_reason,
                    'override_applied': booking.override_applied,
                    'created_at': booking.created_at.isoformat(),
                    'updated_at': booking.updated_at.isoformat(),
                }
                
                # Send confirmation email asynchronously (don't block response)
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    import threading
                    
                    def send_email_async():
                        try:
                            print(f"[EMAIL] Starting email send to {client.email}")
                            
                            # Try Resend first, fallback to SMTP
                            from django.conf import settings
                            resend_api_key = getattr(settings, 'RESEND_API_KEY', None)
                            
                            use_resend = resend_api_key and resend_api_key.strip()
                            
                            if use_resend:
                                print(f"[EMAIL] Using Resend API")
                                import resend
                                resend.api_key = resend_api_key
                            else:
                                print(f"[EMAIL] Resend not configured, using SMTP")
                            
                            subject = f'Booking Confirmation - {service.name}'
                            message = f"""Dear {client.name},

Your appointment has been confirmed!

Booking Details:
- Service: {service.name}
- Staff: {staff.name}
- Date: {start_datetime.strftime('%A, %B %d, %Y')}
- Time: {start_datetime.strftime('%H:%M')}
- Duration: {service.duration_minutes} minutes
- Price: £{service.price}

Reference: #{booking.id}

If you need to cancel or reschedule, please contact us.

Thank you,
{getattr(settings, 'EMAIL_BRAND_NAME', 'NBNE Business Platform')}"""
                            
                            if use_resend:
                                # Use Resend API
                                from_email = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
                                params = {
                                    "from": f"{getattr(settings, 'EMAIL_BRAND_NAME', 'NBNE Business Platform')} <{from_email}>",
                                    "to": [client.email],
                                    "subject": subject,
                                    "text": message
                                }
                                email = resend.Emails.send(params)
                                print(f"[EMAIL] Successfully sent via Resend to {client.email}, ID: {email.get('id')}")
                            else:
                                # Use Django SMTP
                                from django.core.mail import send_mail
                                send_mail(
                                    subject=subject,
                                    message=message,
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    recipient_list=[client.email],
                                    fail_silently=False,
                                )
                                print(f"[EMAIL] Successfully sent via SMTP to {client.email}")
                        except Exception as e:
                            print(f"[EMAIL] ERROR: {type(e).__name__}: {str(e)}")
                            import traceback
                            print(f"[EMAIL] Traceback: {traceback.format_exc()}")
                    
                    # Start email sending in background thread
                    email_thread = threading.Thread(target=send_email_async)
                    email_thread.daemon = True
                    email_thread.start()
                except Exception as e:
                    print(f"Failed to start email thread: {e}")
                
                # Return booking data immediately
                return Response(response_data, status=status.HTTP_201_CREATED)
            
        except (Staff.DoesNotExist, Service.DoesNotExist):
            return Response(
                {'error': 'Invalid staff or service ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create booking: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def slots(self, request):
        """
        Get available time slots for booking.
        Query params: staff_id, service_id, date (YYYY-MM-DD)
        """
        staff_id = request.query_params.get('staff_id')
        service_id = request.query_params.get('service_id')
        date = request.query_params.get('date')
        
        if not all([staff_id, service_id, date]):
            return Response(
                {'error': 'staff_id, service_id, and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        slots = generate_time_slots(staff_id, service_id, date)
        return Response({'slots': slots})
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def available_dates(self, request):
        """
        Get dates with available slots.
        Query params: staff_id, service_id, days_ahead (optional, default 30)
        """
        staff_id = request.query_params.get('staff_id')
        service_id = request.query_params.get('service_id')
        days_ahead = int(request.query_params.get('days_ahead', 30))
        
        if not all([staff_id, service_id]):
            return Response(
                {'error': 'staff_id and service_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dates = get_available_dates(staff_id, service_id, days_ahead)
        return Response({'available_dates': dates})


    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """POST /api/bookings/<id>/cancel/ — Cancel a booking, freeing the slot"""
        booking = self.get_object()
        old_status = booking.status
        if booking.status in ('cancelled', 'completed'):
            return Response(
                {'error': f'Cannot cancel a {booking.status} booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        booking.status = 'cancelled'
        booking.notes = (booking.notes or '') + f'\nCancelled by admin.'
        booking.save()
        try:
            from .smart_engine import on_booking_status_change
            on_booking_status_change(booking, old_status, 'cancelled')
        except Exception:
            pass
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=['post'], url_path='no-show')
    def no_show(self, request, pk=None):
        """POST /api/bookings/<id>/no-show/ — Mark as no-show"""
        booking = self.get_object()
        old_status = booking.status
        booking.status = 'no_show'
        booking.save()
        try:
            from .smart_engine import on_booking_status_change
            on_booking_status_change(booking, old_status, 'no_show')
        except Exception:
            pass
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """POST /api/bookings/<id>/complete/ — Mark as completed"""
        booking = self.get_object()
        old_status = booking.status
        booking.status = 'completed'
        booking.save()
        try:
            from .smart_engine import on_booking_status_change
            on_booking_status_change(booking, old_status, 'completed')
        except Exception:
            pass
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=['post'], url_path='update-notes')
    def update_notes(self, request, pk=None):
        """POST /api/bookings/<id>/update-notes/ — Update booking internal notes"""
        booking = self.get_object()
        notes = request.data.get('notes', '')
        booking.notes = notes
        booking.save(update_fields=['notes', 'updated_at'])
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=['post'], url_path='update-client-notes')
    def update_client_notes(self, request, pk=None):
        """POST /api/bookings/<id>/update-client-notes/ — Update client profile notes"""
        booking = self.get_object()
        notes = request.data.get('notes', '')
        booking.client.notes = notes
        booking.client.save(update_fields=['notes', 'updated_at'])
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=['post'])
    def override(self, request, pk=None):
        """POST /api/bookings/<id>/override/ — Owner overrides SBE recommendation"""
        booking = self.get_object()
        reason = request.data.get('reason', '')
        if not reason:
            return Response({'error': 'Override reason is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from .smart_engine import log_override
            log_override(booking, reason)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(BookingSerializer(booking).data)


class StaffBlockViewSet(viewsets.ModelViewSet):
    """CRUD for staff time blocks (unavailability)"""
    serializer_class = None  # We'll use manual serialization

    def get_queryset(self):
        qs = StaffBlock.objects.select_related('staff').all()
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        return qs

    def _serialize(self, block):
        d = block.date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)
        return {
            'id': block.id,
            'staff': block.staff_id,
            'staff_name': block.staff.name,
            'date': date_str,
            'start_time': block.start_time.strftime('%H:%M') if block.start_time else None,
            'end_time': block.end_time.strftime('%H:%M') if block.end_time else None,
            'reason': block.reason,
            'all_day': block.all_day,
            'created_at': block.created_at.isoformat() if hasattr(block.created_at, 'isoformat') else str(block.created_at),
        }

    def list(self, request):
        blocks = self.get_queryset()
        return Response([self._serialize(b) for b in blocks])

    def _parse_time(self, t_str):
        from datetime import time as dt_time
        if not t_str:
            return dt_time(9, 0)
        parts = t_str.split(':')
        return dt_time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)

    def create(self, request):
        d = request.data
        try:
            staff = Staff.objects.get(id=d.get('staff_id') or d.get('staff'))
        except Staff.DoesNotExist:
            return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            from datetime import time as dt_time, date as dt_date
            all_day = d.get('all_day', False)
            if isinstance(all_day, str):
                all_day = all_day.lower() in ('true', '1', 'yes')
            if all_day:
                start_t = dt_time(0, 0)
                end_t = dt_time(23, 59)
            else:
                start_t = self._parse_time(d.get('start_time', '09:00'))
                end_t = self._parse_time(d.get('end_time', '17:00'))

            # Parse date string to date object
            date_str = d.get('date', '')
            parts = date_str.split('-')
            block_date = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))

            block = StaffBlock.objects.create(
                staff=staff,
                date=block_date,
                start_time=start_t,
                end_time=end_t,
                reason=d.get('reason', ''),
                all_day=all_day,
            )
            block.refresh_from_db()
            block.staff = staff  # re-attach for serialization
            return Response(self._serialize(block), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Failed to create block: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            block = StaffBlock.objects.get(id=pk)
        except StaffBlock.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.filter(active=True)
    serializer_class = SessionSerializer
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming sessions"""
        from django.utils import timezone
        sessions = Session.objects.filter(
            active=True,
            start_time__gte=timezone.now()
        ).order_by('start_time')
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Enroll a client in a session"""
        session = self.get_object()
        client_id = request.data.get('client_id')
        
        if not client_id:
            return Response(
                {'error': 'client_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Client not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if session.is_full:
            return Response(
                {'error': 'Session is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.enrolled_clients.add(client)
        serializer = self.get_serializer(session)
        return Response(serializer.data)
