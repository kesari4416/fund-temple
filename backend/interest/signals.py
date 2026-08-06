"""
Signal handlers for the ``interest`` app.

Owner rule (Feb 2026 — locked): whenever ``PeopleInterestDetails.paid_counts``
changes, keep the rolling ``installment_date`` pointer in lock-step so the
overdue-penalty walker stays accurate.

Rule
----
::

    installment_date  =  interest_date  +  (period_delta × (paid_counts + 1))

- ``paid_counts = 0``  ->  first upcoming due date  (1 cadence step after start)
- ``paid_counts = 1``  ->  second upcoming due date (2 steps after start)
- and so on

Scope
-----
Applies ONLY to loans where
``interest_type == 'Chit fund Interest'`` AND
``interest_category == 'Installment Interest'`` AND
``interest_date IS NOT NULL`` AND the cadence fields are populated.

This one signal replaces the need to edit every ``collection/views.py``
site that touches ``paid_counts`` (add, edit, delete). Any future write
path automatically gets the pointer updated for free.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PeopleInterestDetails


@receiver(post_save, sender=PeopleInterestDetails)
def sync_installment_date(sender, instance, created, update_fields, **kwargs):
    # Skip signal-driven writes that only touched installment_date itself
    # (prevents infinite recursion).
    if update_fields and set(update_fields) <= {"installment_date"}:
        return

    # Scope guard — only Chit-Fund Installment loans carry a pointer.
    if instance.interest_type != "Chit fund Interest":
        return
    if instance.interest_category != "Installment Interest":
        return
    if not instance.interest_date:
        return

    # Local import so the app can boot before overdue_views is loaded.
    try:
        from interest.overdue_views import _installment_delta
    except Exception:
        return

    delta = _installment_delta(instance)
    if not delta:
        return

    paid_counts = int(instance.paid_counts or 0)
    target = instance.interest_date + (delta * (paid_counts + 1))
    if instance.installment_date == target:
        return

    # QuerySet.update() bypasses save() so we don't re-enter this signal.
    PeopleInterestDetails.objects.filter(pk=instance.pk).update(
        installment_date=target
    )
