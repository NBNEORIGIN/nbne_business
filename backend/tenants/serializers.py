from rest_framework import serializers
from .models import TenantSettings


class TenantSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantSettings
        fields = [
            'slug', 'business_name', 'business_type', 'enabled_modules',
            'tagline', 'logo_url', 'favicon_url',
            'colour_primary', 'colour_secondary', 'colour_accent',
            'colour_background', 'colour_text',
            'font_heading', 'font_body', 'font_url',
            'email', 'phone', 'address', 'website_url',
            'social_facebook', 'social_instagram', 'social_twitter',
            'business_hours',
            'booking_staff_label', 'booking_staff_label_plural',
            'booking_lead_time_hours', 'booking_max_advance_days',
            'cancellation_policy', 'deposit_percentage',
            'currency', 'currency_symbol',
            'pwa_theme_colour', 'pwa_background_colour', 'pwa_short_name',
        ]
        read_only_fields = fields


class TenantSettingsUpdateSerializer(serializers.ModelSerializer):
    """Writable serializer for owner updates."""
    class Meta:
        model = TenantSettings
        fields = [
            'business_name', 'business_type', 'tagline', 'logo_url', 'favicon_url',
            'colour_primary', 'colour_secondary', 'colour_accent',
            'colour_background', 'colour_text',
            'font_heading', 'font_body', 'font_url',
            'email', 'phone', 'address', 'website_url',
            'social_facebook', 'social_instagram', 'social_twitter',
            'business_hours',
            'booking_lead_time_hours', 'booking_max_advance_days',
            'cancellation_policy', 'deposit_percentage',
            'currency', 'currency_symbol',
            'booking_staff_label', 'booking_staff_label_plural',
        ]


class TenantSettingsCSSVarsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantSettings
        fields = [
            'slug', 'business_name', 'business_type', 'enabled_modules',
            'tagline', 'logo_url', 'favicon_url',
            'colour_primary', 'colour_secondary', 'colour_accent',
            'colour_background', 'colour_text',
            'font_heading', 'font_body', 'font_url',
            'currency_symbol',
            'phone', 'email',
            'booking_staff_label', 'booking_staff_label_plural',
            'pwa_theme_colour', 'pwa_background_colour', 'pwa_short_name',
        ]
        read_only_fields = fields
