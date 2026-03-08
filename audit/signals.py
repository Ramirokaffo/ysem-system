from django.apps import apps
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save

from .context import is_audit_suspended
from .utils import diff_states, is_auditable_model, log_audit_event, serialize_instance


SIGNALS_REGISTERED = False


def capture_previous_state(sender, instance, raw=False, **kwargs):
    if raw or is_audit_suspended() or not is_auditable_model(sender) or not instance.pk:
        return
    try:
        previous = sender._default_manager.get(pk=instance.pk)
    except sender.DoesNotExist:
        previous = None
    instance._audit_previous_state = serialize_instance(previous)


def audit_save(sender, instance, created, raw=False, **kwargs):
    if raw or is_audit_suspended() or not is_auditable_model(sender):
        return
    current_state = serialize_instance(instance)
    previous_state = getattr(instance, "_audit_previous_state", {}) or {}
    changes = diff_states(previous_state, current_state)
    if created:
        changes = {key: {"from": None, "to": value} for key, value in current_state.items()}
    elif not changes:
        return
    log_audit_event(
        category="model",
        action="create" if created else "update",
        instance=instance,
        changes=changes,
        context={"snapshot": current_state},
        message=f"{'Création' if created else 'Modification'} de {instance._meta.object_name}",
    )
    if hasattr(instance, "_audit_previous_state"):
        delattr(instance, "_audit_previous_state")


def audit_delete(sender, instance, **kwargs):
    if is_audit_suspended() or not is_auditable_model(sender):
        return
    snapshot = serialize_instance(instance)
    log_audit_event(
        category="model",
        action="delete",
        instance=instance,
        context={"snapshot": snapshot},
        message=f"Suppression de {instance._meta.object_name}",
    )


def audit_m2m(sender, instance, action, reverse, model, pk_set, **kwargs):
    if is_audit_suspended() or not is_auditable_model(instance.__class__) or action not in {"post_add", "post_remove", "post_clear"}:
        return
    field_name = next(
        (field.name for field in instance._meta.many_to_many if field.remote_field.through is sender),
        sender._meta.model_name,
    )
    log_audit_event(
        category="m2m",
        action=action.replace("post_", "m2m_"),
        instance=instance,
        context={
            "field": field_name,
            "related_model": model._meta.label,
            "related_ids": sorted(pk_set) if pk_set else [],
            "reverse": reverse,
        },
        message=f"Modification M2M sur {instance._meta.object_name}.{field_name}",
    )


def register_audit_signals():
    global SIGNALS_REGISTERED
    if SIGNALS_REGISTERED:
        return
    for model in apps.get_models():
        if not is_auditable_model(model):
            continue
        pre_save.connect(capture_previous_state, sender=model, weak=False, dispatch_uid=f"audit_pre_save_{model._meta.label_lower}")
        post_save.connect(audit_save, sender=model, weak=False, dispatch_uid=f"audit_post_save_{model._meta.label_lower}")
        post_delete.connect(audit_delete, sender=model, weak=False, dispatch_uid=f"audit_post_delete_{model._meta.label_lower}")
        for field in model._meta.many_to_many:
            m2m_changed.connect(audit_m2m, sender=field.remote_field.through, weak=False, dispatch_uid=f"audit_m2m_{model._meta.label_lower}_{field.name}")
    SIGNALS_REGISTERED = True
