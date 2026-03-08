import json
import logging
from decimal import Decimal
from functools import lru_cache
from uuid import UUID

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import File
from django.db import DatabaseError, OperationalError, ProgrammingError, connection
from django.db.models import Model

from .context import get_actor_override, get_current_request, suspend_audit
from .models import AuditLog


logger = logging.getLogger("audit")
EXCLUDED_APPS = {"audit", "corsheaders", "rest_framework", "rest_framework_simplejwt"}
EXCLUDED_FIELDS = {"created_at", "updated_at", "last_updated", "last_modified", "last_login"}
SENSITIVE_TOKENS = ("password", "secret", "token", "api_key", "session")


def is_auditable_model(model_or_instance):
    model = model_or_instance if hasattr(model_or_instance, "_meta") and hasattr(model_or_instance._meta, "app_config") else model_or_instance.__class__
    app_name = model._meta.app_config.name
    return not app_name.startswith("django.") and app_name not in EXCLUDED_APPS and model._meta.label_lower != "audit.auditlog"


def is_sensitive_field(field_name):
    lowered = field_name.lower()
    return any(token in lowered for token in SENSITIVE_TOKENS)


def normalize_value(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, File):
        return value.name or None
    if isinstance(value, Model):
        return str(value.pk)
    return str(value)


def serialize_instance(instance):
    if instance is None or not hasattr(instance, "_meta"):
        return {}
    data = {}
    for field in instance._meta.concrete_fields:
        if field.name in EXCLUDED_FIELDS or is_sensitive_field(field.name):
            continue
        data[field.name] = normalize_value(field.value_from_object(instance))
    return data


def diff_states(before, after):
    changes = {}
    for key in sorted(set(before) | set(after)):
        old_value = before.get(key)
        new_value = after.get(key)
        if old_value != new_value:
            changes[key] = {"from": old_value, "to": new_value}
    return changes


def get_request_details(request=None):
    request = request or get_current_request()
    if request is None:
        return {}
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")
    return {
        "request_method": request.method,
        "request_path": request.get_full_path(),
        "ip_address": ip_address,
        "user_agent": (request.META.get("HTTP_USER_AGENT") or "")[:255],
    }


def resolve_actor(actor=None, request=None, actor_identifier="", actor_display=""):
    actor = actor or get_actor_override()
    request = request or get_current_request()
    if actor is None and request is not None:
        request_user = getattr(request, "user", None)
        if getattr(request_user, "is_authenticated", False):
            actor = request_user

    payload = {
        "actor_type": "",
        "actor_user": None,
        "actor_agent_id": None,
        "actor_identifier": actor_identifier or "",
        "actor_display": actor_display or "",
    }
    if actor is None:
        payload["actor_type"] = "anonymous"
        return payload

    if hasattr(actor, "agent"):
        agent = actor.agent
        payload.update(
            actor_type="agent",
            actor_agent_id=agent.pk,
            actor_identifier=agent.email or agent.matricule,
            actor_display=agent.nom_complet,
        )
        return payload

    if getattr(actor, "_meta", None) and actor._meta.label_lower == settings.AUTH_USER_MODEL.lower():
        payload.update(
            actor_type="user",
            actor_user=actor,
            actor_identifier=actor.username,
            actor_display=actor.get_full_name() or actor.username,
        )
        return payload

    if getattr(actor, "_meta", None) and actor._meta.label_lower == "prospection.agent":
        payload.update(
            actor_type="agent",
            actor_agent_id=actor.pk,
            actor_identifier=actor.email or actor.matricule,
            actor_display=getattr(actor, "nom_complet", str(actor)),
        )
        return payload

    payload["actor_type"] = actor.__class__.__name__.lower()
    payload["actor_display"] = actor_display or str(actor)
    return payload


def build_target_payload(instance=None, target=None):
    payload = {
        "target_content_type": None,
        "target_object_id": "",
        "target_repr": "",
        "target_app_label": "",
        "target_model": "",
    }
    if instance is not None and hasattr(instance, "_meta"):
        payload.update(
            target_object_id=str(instance.pk),
            target_repr=str(instance)[:255],
            target_app_label=instance._meta.app_label,
            target_model=instance._meta.object_name,
        )
        try:
            payload["target_content_type"] = ContentType.objects.get_for_model(instance, for_concrete_model=False)
        except Exception:
            pass
        return payload
    if target:
        payload.update({key: value for key, value in target.items() if key in payload})
    return payload


@lru_cache(maxsize=1)
def system_settings_table_exists():
    return "main_systemsettings" in connection.introspection.table_names()


def is_audit_enabled(instance=None):
    if instance is not None and getattr(instance, "_meta", None) and instance._meta.label_lower == "audit.auditlog":
        return False
    if instance is not None and getattr(instance, "_meta", None) and instance._meta.label_lower == "main.systemsettings":
        return True
    try:
        if not system_settings_table_exists():
            return True
        with connection.cursor():
            from main.models import SystemSettings

            value = SystemSettings.objects.filter(pk=1).values_list("audit_log", flat=True).first()
            return True if value is None else bool(value)
    except Exception:
        return True


def log_audit_event(*, category, action, instance=None, actor=None, changes=None, context=None, message="", force=False, target=None, actor_identifier="", actor_display=""):
    if not force and not is_audit_enabled(instance):
        return None

    payload = {
        "category": category,
        "action": action,
        "message": message,
        "changes": changes or {},
        "context": context or {},
    }
    payload.update(resolve_actor(actor=actor, actor_identifier=actor_identifier, actor_display=actor_display))
    payload.update(build_target_payload(instance=instance, target=target))
    payload.update(get_request_details())

    try:
        with suspend_audit():
            entry = AuditLog.objects.create(**payload)
    except (DatabaseError, OperationalError, ProgrammingError):
        logger.warning("Impossible d'écrire dans le journal d'audit.")
        return None

    logger.info(json.dumps({
        "category": category,
        "action": action,
        "actor": payload.get("actor_identifier") or payload.get("actor_display"),
        "target": payload.get("target_repr"),
        "path": payload.get("request_path"),
        "message": message,
    }, ensure_ascii=False, default=str))
    return entry
