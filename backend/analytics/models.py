from django.db import models


class Recommendation(models.Model):
    TYPE_CHOICES = [
        ('REVENUE', 'Revenue'), ('EFFICIENCY', 'Efficiency'),
        ('MARKETING', 'Marketing'), ('COMPLIANCE', 'Compliance'),
        ('STAFFING', 'Staffing'), ('OTHER', 'Other'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    recommendation_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='OTHER', db_index=True)
    priority = models.IntegerField(default=0)
    is_dismissed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_recommendation'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"[{self.get_recommendation_type_display()}] {self.title}"
