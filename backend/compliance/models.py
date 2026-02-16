from django.conf import settings
from django.db import models


class IncidentReport(models.Model):
    SEVERITY_CHOICES = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')]
    STATUS_CHOICES = [('OPEN', 'Open'), ('INVESTIGATING', 'Investigating'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, null=True, blank=True, related_name='incidents')
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    location = models.CharField(max_length=255, blank=True, default='')
    incident_date = models.DateTimeField(db_index=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    resolution_notes = models.TextField(blank=True, default='')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-incident_date']
        verbose_name = 'Incident Report'
        verbose_name_plural = 'Incident Reports'

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"


class IncidentPhoto(models.Model):
    incident = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='compliance/incidents/%Y/%m/')
    caption = models.CharField(max_length=255, blank=True, default='')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Incident Photo'
        verbose_name_plural = 'Incident Photos'

    def __str__(self):
        return f"Photo for {self.incident.title}"


class SignOff(models.Model):
    incident = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, related_name='sign_offs')
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-signed_at']
        verbose_name = 'Sign Off'
        verbose_name_plural = 'Sign Offs'

    def __str__(self):
        signer = self.signed_by.get_full_name() if self.signed_by else 'Unknown'
        return f"Sign-off by {signer} on {self.incident.title}"


class RiskAssessment(models.Model):
    STATUS_CHOICES = [('CURRENT', 'Current'), ('REVIEW_DUE', 'Review Due'), ('EXPIRED', 'Expired'), ('DRAFT', 'Draft')]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, null=True, blank=True, related_name='risk_assessments')
    title = models.CharField(max_length=255)
    site_area = models.CharField(max_length=255, help_text='Area or location assessed')
    assessor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assessments')
    assessment_date = models.DateField()
    review_date = models.DateField(help_text='Next review due date')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CURRENT', db_index=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-assessment_date']
        verbose_name = 'Risk Assessment'
        verbose_name_plural = 'Risk Assessments'

    def __str__(self):
        return f"{self.title} — {self.site_area}"

    @property
    def findings_count(self):
        return self.findings.count()

    @property
    def high_risk_count(self):
        return self.findings.filter(severity__in=['HIGH', 'CRITICAL']).count()

    @property
    def is_review_due(self):
        from django.utils import timezone
        return self.review_date <= timezone.now().date()


class HazardFinding(models.Model):
    SEVERITY_CHOICES = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')]
    STATUS_CHOICES = [('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('RESOLVED', 'Resolved'), ('ACCEPTED', 'Risk Accepted')]

    assessment = models.ForeignKey(RiskAssessment, on_delete=models.CASCADE, related_name='findings')
    category = models.CharField(max_length=255, help_text='e.g. Fire Safety, Slips/Trips, Chemical Handling')
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM', db_index=True)
    confidence = models.FloatField(default=1.0, help_text='Confidence level 0.0–1.0')
    control_measures = models.TextField(blank=True, default='', help_text='Control measures, one per line')
    regulatory_ref = models.CharField(max_length=255, blank=True, default='', help_text='e.g. HSE INDG225, COSHH Reg 7')
    evidence_url = models.URLField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_findings')
    due_date = models.DateField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Hazard Finding'
        verbose_name_plural = 'Hazard Findings'

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.category} — {self.description[:60]}"


class Equipment(models.Model):
    STATUS_CHOICES = [('OK', 'OK'), ('DUE_SOON', 'Inspection Due Soon'), ('OVERDUE', 'Overdue'), ('OUT_OF_SERVICE', 'Out of Service')]
    CATEGORY_CHOICES = [
        ('FIRE_SAFETY', 'Fire Safety'),
        ('FIRST_AID', 'First Aid'),
        ('ELECTRICAL', 'Electrical'),
        ('VENTILATION', 'Ventilation'),
        ('SECURITY', 'Security'),
        ('WELLNESS', 'Wellness Equipment'),
        ('OTHER', 'Other'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, null=True, blank=True, related_name='equipment')
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='OTHER', db_index=True)
    serial_number = models.CharField(max_length=100, blank=True, default='')
    last_inspection = models.DateField(null=True, blank=True)
    next_inspection = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OK', db_index=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_inspection']
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'

    def __str__(self):
        return f"{self.name} — {self.location}"

    @property
    def is_overdue(self):
        if not self.next_inspection:
            return False
        from django.utils import timezone
        return self.next_inspection < timezone.now().date()

    def save(self, *args, **kwargs):
        # Auto-update status based on inspection dates
        if self.next_inspection:
            from django.utils import timezone
            from datetime import timedelta
            today = timezone.now().date()
            if self.next_inspection < today:
                self.status = 'OVERDUE'
            elif self.next_inspection <= today + timedelta(days=30):
                self.status = 'DUE_SOON'
        super().save(*args, **kwargs)


class EquipmentInspection(models.Model):
    RESULT_CHOICES = [('PASS', 'Pass'), ('FAIL', 'Fail'), ('ADVISORY', 'Advisory')]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='inspections')
    inspection_date = models.DateField()
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='PASS')
    notes = models.TextField(blank=True, default='')
    next_due = models.DateField(null=True, blank=True, help_text='Sets next inspection date on equipment')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-inspection_date']
        verbose_name = 'Equipment Inspection'
        verbose_name_plural = 'Equipment Inspections'

    def __str__(self):
        return f"{self.equipment.name} — {self.inspection_date} ({self.get_result_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update equipment inspection dates
        self.equipment.last_inspection = self.inspection_date
        if self.next_due:
            self.equipment.next_inspection = self.next_due
        self.equipment.save()


class ComplianceCategory(models.Model):
    """Categories for compliance scoring (e.g. Fire Safety, Chemical Handling)"""
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, null=True, blank=True, related_name='compliance_categories')
    name = models.CharField(max_length=255)
    max_score = models.IntegerField(default=10)
    current_score = models.IntegerField(default=0)
    notes = models.TextField(blank=True, default='')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Compliance Category'
        verbose_name_plural = 'Compliance Categories'

    def __str__(self):
        return f"{self.name} ({self.current_score}/{self.max_score})"

    @property
    def percentage(self):
        return round((self.current_score / self.max_score) * 100) if self.max_score > 0 else 0


class ComplianceItem(models.Model):
    """
    Individual compliance item that contributes to the Peace of Mind Score.
    Each item has a type (LEGAL or BEST_PRACTICE) and a status.
    Enhanced with frequency, evidence, and completion tracking.
    """
    TYPE_CHOICES = [
        ('LEGAL', 'Legal Requirement'),
        ('BEST_PRACTICE', 'Best Practice'),
    ]
    STATUS_CHOICES = [
        ('COMPLIANT', 'Compliant'),
        ('DUE_SOON', 'Due Soon'),
        ('OVERDUE', 'Overdue'),
    ]
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('biennial', 'Every 2 Years'),
        ('5_year', 'Every 5 Years'),
        ('ad_hoc', 'Ad Hoc / One-off'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    category = models.ForeignKey(ComplianceCategory, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='BEST_PRACTICE', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLIANT', db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    regulatory_ref = models.CharField(max_length=255, blank=True, default='', help_text='Legal/regulatory reference')
    legal_reference = models.CharField(max_length=500, blank=True, default='', help_text='Full legal reference e.g. Regulatory Reform (Fire Safety) Order 2005')
    notes = models.TextField(blank=True, default='')
    # Frequency and scheduling
    frequency_type = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='annual', db_index=True)
    last_completed_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True, db_index=True)
    # Evidence
    evidence_required = models.BooleanField(default=False, help_text='Whether evidence upload is required on completion')
    document = models.FileField(upload_to='compliance/evidence/%Y/%m/', null=True, blank=True, help_text='Latest evidence document')
    completed_by = models.CharField(max_length=255, blank=True, default='', help_text='Name of person who completed')
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'item_type', 'title']
        verbose_name = 'Compliance Item'
        verbose_name_plural = 'Compliance Items'

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.title} — {self.get_status_display()}"

    @property
    def weight(self):
        """LEGAL items weight 2, BEST_PRACTICE weight 1"""
        return 2 if self.item_type == 'LEGAL' else 1

    @property
    def status_factor(self):
        """COMPLIANT=1.0, DUE_SOON=0.5, OVERDUE=0.0"""
        if self.status == 'COMPLIANT':
            return 1.0
        elif self.status == 'DUE_SOON':
            return 0.5
        return 0.0

    @property
    def achieved_weight(self):
        return self.weight * self.status_factor

    def _ensure_date(self, val):
        """Convert string to date if needed."""
        if val and isinstance(val, str):
            from datetime import date as dt_date
            try:
                parts = val.split('-')
                return dt_date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                return None
        return val

    def compute_status(self):
        """Compute status from next_due_date"""
        if not self.next_due_date:
            return 'COMPLIANT'
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        due = self._ensure_date(self.next_due_date)
        if not due:
            return 'COMPLIANT'
        if due < today:
            return 'OVERDUE'
        elif due <= today + timedelta(days=30):
            return 'DUE_SOON'
        return 'COMPLIANT'

    def compute_next_due(self):
        """Calculate next_due_date from last_completed_date + frequency"""
        if not self.last_completed_date or self.frequency_type == 'ad_hoc':
            return self.next_due_date
        try:
            from dateutil.relativedelta import relativedelta
        except ImportError:
            from datetime import timedelta
            # Fallback if python-dateutil not installed
            freq_days = {'monthly': 30, 'quarterly': 91, 'annual': 365, 'biennial': 730, '5_year': 1826}
            days = freq_days.get(self.frequency_type, 365)
            return self.last_completed_date + timedelta(days=days)
        freq_map = {
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'annual': relativedelta(years=1),
            'biennial': relativedelta(years=2),
            '5_year': relativedelta(years=5),
        }
        delta = freq_map.get(self.frequency_type)
        if delta:
            return self.last_completed_date + delta
        return self.next_due_date

    def save(self, *args, **kwargs):
        # Ensure date fields are actual date objects
        self.next_due_date = self._ensure_date(self.next_due_date)
        self.last_completed_date = self._ensure_date(self.last_completed_date)
        # Auto-compute status from dates
        computed = self.compute_status()
        if computed != self.status:
            self.status = computed
        # Sync due_date with next_due_date for backward compat
        if self.next_due_date:
            self.due_date = self.next_due_date
        super().save(*args, **kwargs)


class AccidentReport(models.Model):
    """
    UK-compliant accident/incident log with RIDDOR support.
    Separate from IncidentReport which is for general H&S incidents.
    """
    SEVERITY_CHOICES = [
        ('MINOR', 'Minor (First Aid)'),
        ('MODERATE', 'Moderate (Medical Attention)'),
        ('MAJOR', 'Major (Hospital)'),
        ('FATAL', 'Fatal'),
    ]
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Under Investigation'),
        ('FOLLOW_UP', 'Follow-up Required'),
        ('CLOSED', 'Closed'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, null=True, blank=True, related_name='accident_reports')
    date = models.DateField(db_index=True)
    time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, default='')
    person_involved = models.CharField(max_length=255, help_text='Name of person involved')
    person_role = models.CharField(max_length=100, blank=True, default='', help_text='e.g. Staff, Client, Visitor')
    description = models.TextField(help_text='Full description of the accident/incident')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MINOR', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    # RIDDOR
    riddor_reportable = models.BooleanField(default=False, help_text='Is this reportable under RIDDOR?')
    hse_reference = models.CharField(max_length=100, blank=True, default='', help_text='HSE reference number if reported')
    riddor_reported_date = models.DateField(null=True, blank=True)
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True, default='')
    follow_up_completed = models.BooleanField(default=False)
    follow_up_completed_date = models.DateField(null=True, blank=True)
    # Evidence
    document = models.FileField(upload_to='compliance/accidents/%Y/%m/', null=True, blank=True)
    # Metadata
    reported_by = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Accident Report'
        verbose_name_plural = 'Accident Reports'

    def __str__(self):
        return f"{self.date} — {self.person_involved} ({self.get_severity_display()})"


class PeaceOfMindScore(models.Model):
    """
    Cached Peace of Mind Score (0–100).
    Single row per tenant — recalculated on item changes and daily.
    """
    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, null=True, blank=True, related_name='peace_of_mind_scores')
    score = models.IntegerField(default=0)
    previous_score = models.IntegerField(default=0)
    total_items = models.IntegerField(default=0)
    compliant_count = models.IntegerField(default=0)
    due_soon_count = models.IntegerField(default=0)
    overdue_count = models.IntegerField(default=0)
    legal_items = models.IntegerField(default=0)
    best_practice_items = models.IntegerField(default=0)
    last_calculated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Peace of Mind Score'
        verbose_name_plural = 'Peace of Mind Score'

    def __str__(self):
        return f"Peace of Mind Score: {self.score}%"

    @property
    def score_change(self):
        return self.score - self.previous_score

    @property
    def interpretation(self):
        if self.score >= 90:
            return "Your compliance is in strong shape."
        elif self.score >= 70:
            return "A few items need attention soon."
        else:
            return "There are overdue compliance items."

    @property
    def colour(self):
        if self.score >= 80:
            return 'green'
        elif self.score >= 60:
            return 'amber'
        return 'red'

    @classmethod
    def recalculate(cls):
        """
        Core scoring algorithm:
        Total possible weight = sum(all item weights)
        Achieved weight = sum(weight * status_factor)
        Score = (achieved / total) * 100, rounded to nearest int
        """
        from django.utils import timezone

        items = ComplianceItem.objects.all()
        total_possible = 0
        achieved = 0
        compliant = 0
        due_soon = 0
        overdue = 0
        legal = 0
        best_practice = 0

        for item in items:
            total_possible += item.weight
            achieved += item.achieved_weight

            if item.status == 'COMPLIANT':
                compliant += 1
            elif item.status == 'DUE_SOON':
                due_soon += 1
            else:
                overdue += 1

            if item.item_type == 'LEGAL':
                legal += 1
            else:
                best_practice += 1

        new_score = round((achieved / total_possible) * 100) if total_possible > 0 else 100

        obj, created = cls.objects.get_or_create(pk=1, defaults={
            'score': new_score,
            'previous_score': 0,
            'total_items': items.count(),
            'compliant_count': compliant,
            'due_soon_count': due_soon,
            'overdue_count': overdue,
            'legal_items': legal,
            'best_practice_items': best_practice,
        })

        if not created:
            obj.previous_score = obj.score
            obj.score = new_score
            obj.total_items = items.count()
            obj.compliant_count = compliant
            obj.due_soon_count = due_soon
            obj.overdue_count = overdue
            obj.legal_items = legal
            obj.best_practice_items = best_practice
            obj.save()

        # Log the recalculation
        ScoreAuditLog.objects.create(
            score=new_score,
            previous_score=obj.previous_score if not created else 0,
            total_items=items.count(),
            compliant_count=compliant,
            due_soon_count=due_soon,
            overdue_count=overdue,
            trigger='auto',
        )

        # Update ComplianceCategory scores based on their items
        for cat in ComplianceCategory.objects.all():
            cat_items = cat.items.all()
            cat_total = sum(i.weight for i in cat_items)
            cat_achieved = sum(i.achieved_weight for i in cat_items)
            cat.current_score = round((cat_achieved / cat_total) * cat.max_score) if cat_total > 0 else cat.max_score
            cat.save()

        return obj


class ScoreAuditLog(models.Model):
    """Audit log for every score recalculation"""
    TRIGGER_CHOICES = [
        ('auto', 'Automatic (item change)'),
        ('manual', 'Manual recalculation'),
        ('scheduled', 'Scheduled (daily)'),
    ]

    score = models.IntegerField()
    previous_score = models.IntegerField()
    total_items = models.IntegerField()
    compliant_count = models.IntegerField()
    due_soon_count = models.IntegerField()
    overdue_count = models.IntegerField()
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES, default='auto')
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-calculated_at']
        verbose_name = 'Score Audit Log'
        verbose_name_plural = 'Score Audit Logs'

    def __str__(self):
        change = self.score - self.previous_score
        direction = f"+{change}" if change > 0 else str(change)
        return f"{self.calculated_at.strftime('%Y-%m-%d %H:%M')} — Score: {self.score}% ({direction})"


class RAMSDocument(models.Model):
    STATUS_CHOICES = [('DRAFT', 'Draft'), ('ACTIVE', 'Active'), ('EXPIRED', 'Expired'), ('ARCHIVED', 'Archived')]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, null=True, blank=True, related_name='rams_documents')
    title = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, blank=True, default='', db_index=True)
    description = models.TextField(blank=True, default='')
    document = models.FileField(upload_to='compliance/rams/%Y/%m/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_rams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'RAMS Document'
        verbose_name_plural = 'RAMS Documents'

    def __str__(self):
        return f"{self.title} ({self.reference_number})" if self.reference_number else self.title

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()
