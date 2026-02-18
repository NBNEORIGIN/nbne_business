from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender='compliance.ComplianceItem')
def recalculate_score_on_save(sender, instance, **kwargs):
    from .models import PeaceOfMindScore, ComplianceItem
    if not isinstance(instance, ComplianceItem):
        return
    tenant = getattr(instance.category, 'tenant', None) if hasattr(instance, 'category_id') and instance.category_id else None
    PeaceOfMindScore.recalculate(tenant=tenant)


@receiver(post_delete, sender='compliance.ComplianceItem')
def recalculate_score_on_delete(sender, instance, **kwargs):
    from .models import PeaceOfMindScore, ComplianceItem
    if not isinstance(instance, ComplianceItem):
        return
    tenant = getattr(instance.category, 'tenant', None) if hasattr(instance, 'category_id') and instance.category_id else None
    PeaceOfMindScore.recalculate(tenant=tenant)
