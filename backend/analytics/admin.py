from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recommendation_type', 'priority', 'is_dismissed', 'created_at']
    list_filter = ['recommendation_type', 'is_dismissed']
    search_fields = ['title']
