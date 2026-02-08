from django.db import models


class TenantSettings(models.Model):
    """Multi-tenant configuration. Each demo site gets its own row."""

    slug = models.SlugField(max_length=100, unique=True, default='default', help_text='URL-safe identifier e.g. salon-x')
    business_name = models.CharField(max_length=255)
    enabled_modules = models.JSONField(
        default=list, blank=True,
        help_text='List of enabled module names e.g. ["bookings","payments","staff"]'
    )
    tagline = models.CharField(max_length=500, blank=True, default='')
    logo_url = models.URLField(blank=True, default='')
    favicon_url = models.URLField(blank=True, default='')

    colour_primary = models.CharField(max_length=50, default='hsl(220, 70%, 50%)')
    colour_secondary = models.CharField(max_length=50, default='hsl(220, 70%, 30%)')
    colour_accent = models.CharField(max_length=50, blank=True, default='')
    colour_background = models.CharField(max_length=50, default='#ffffff')
    colour_text = models.CharField(max_length=50, default='#333333')

    font_heading = models.CharField(max_length=100, default='system-ui')
    font_body = models.CharField(max_length=100, default='system-ui')
    font_url = models.URLField(blank=True, default='')

    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    address = models.TextField(blank=True, default='')
    website_url = models.URLField(blank=True, default='')

    social_facebook = models.URLField(blank=True, default='')
    social_instagram = models.URLField(blank=True, default='')
    social_twitter = models.URLField(blank=True, default='')

    business_hours = models.JSONField(default=dict, blank=True)

    booking_lead_time_hours = models.IntegerField(default=24)
    booking_max_advance_days = models.IntegerField(default=60)
    cancellation_policy = models.TextField(blank=True, default='')
    deposit_percentage = models.IntegerField(default=0)
    currency = models.CharField(max_length=3, default='GBP')
    currency_symbol = models.CharField(max_length=5, default='£')

    pwa_theme_colour = models.CharField(max_length=50, blank=True, default='')
    pwa_background_colour = models.CharField(max_length=50, default='#ffffff')
    pwa_short_name = models.CharField(max_length=30, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants_settings'
        verbose_name = 'Tenant Settings'
        verbose_name_plural = 'Tenant Settings'

    def __str__(self):
        return self.business_name or 'Tenant Settings'

    @classmethod
    def load(cls, slug=None):
        """Load tenant by slug, or return the first tenant as default."""
        if slug:
            return cls.objects.filter(slug=slug).first()
        return cls.objects.first()
