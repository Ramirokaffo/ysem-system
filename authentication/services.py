"""
Services liés à l'historique de connexion et à la détection d'appareils
inconnus (préparation de la double authentification ciblée).
"""
import json
import logging
import re
import socket
import threading
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.utils import timezone

from .models import LoginHistory


logger = logging.getLogger("authentication")

_BROWSER_PATTERNS = [
    ("Edge", r"Edg(?:e|A|iOS)?/([0-9.]+)"),
    ("Opera", r"OPR/([0-9.]+)"),
    ("Chrome", r"Chrome/([0-9.]+)"),
    ("Firefox", r"Firefox/([0-9.]+)"),
    ("Safari", r"Version/([0-9.]+).*Safari"),
    ("Internet Explorer", r"MSIE ([0-9.]+)"),
]

_OS_PATTERNS = [
    ("Windows", r"Windows NT ([0-9.]+)"),
    ("Android", r"Android ([0-9.]+)"),
    ("iOS", r"OS ([0-9_]+) like Mac"),
    ("macOS", r"Mac OS X ([0-9_.]+)"),
    ("Linux", r"(Linux)"),
]

_BOT_RE = re.compile(r"bot|crawler|spider|crawl|slurp|curl|wget|python-requests", re.IGNORECASE)
_MOBILE_RE = re.compile(r"Mobi|Android.+Mobile|iPhone|iPod", re.IGNORECASE)
_TABLET_RE = re.compile(r"iPad|Tablet|Android(?!.*Mobile)", re.IGNORECASE)


def get_client_ip(request):
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def parse_user_agent(ua: str) -> dict:
    ua = ua or ""
    browser_family, browser_version = "", ""
    for name, pattern in _BROWSER_PATTERNS:
        match = re.search(pattern, ua)
        if match:
            browser_family = name
            browser_version = match.group(1) if match.groups() else ""
            break

    os_family, os_version = "", ""
    for name, pattern in _OS_PATTERNS:
        match = re.search(pattern, ua)
        if match:
            os_family = name
            os_version = (match.group(1) if match.groups() else "").replace("_", ".")
            break

    if _BOT_RE.search(ua):
        device_type = "bot"
    elif _TABLET_RE.search(ua):
        device_type = "tablet"
    elif _MOBILE_RE.search(ua):
        device_type = "mobile"
    elif ua:
        device_type = "desktop"
    else:
        device_type = ""

    device_family = ""
    match = re.search(r"\(([^)]+)\)", ua)
    if match:
        device_family = match.group(1).split(";")[0].strip()

    return {
        "browser_family": browser_family[:100],
        "browser_version": browser_version[:50],
        "os_family": os_family[:100],
        "os_version": os_version[:50],
        "device_type": device_type[:20],
        "device_family": device_family[:100],
    }


def build_device_label(parsed: dict) -> str:
    parts = []
    if parsed.get("browser_family"):
        parts.append(parsed["browser_family"])
    if parsed.get("os_family"):
        parts.append(f"sur {parsed['os_family']}")
    device_type = parsed.get("device_type")
    if device_type and device_type not in ("desktop", ""):
        parts.append(f"({device_type})")
    return " ".join(parts)[:255]


def _is_public_ip(ip: str) -> bool:
    if not ip:
        return False
    private_prefixes = ("10.", "192.168.", "127.", "::1", "fc", "fd", "169.254.")
    if any(ip.startswith(prefix) for prefix in private_prefixes):
        return False
    if ip.startswith("172."):
        try:
            second = int(ip.split(".")[1])
            if 16 <= second <= 31:
                return False
        except (ValueError, IndexError):
            return False
    return True


def lookup_location(ip: str, timeout: float = 1.5) -> dict:
    if not _is_public_ip(ip):
        return {}
    url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,query"
    try:
        req = Request(url, headers={"User-Agent": "ysem-login-history"})
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") != "success":
            return {}
        return {
            "country": (data.get("country") or "")[:100],
            "region": (data.get("regionName") or "")[:100],
            "city": (data.get("city") or "")[:100],
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "raw": data,
        }
    except (URLError, socket.timeout, ValueError, OSError) as exc:
        logger.debug("Échec de géolocalisation IP %s: %s", ip, exc)
        return {}



def _resolve_location_async(entry_id: int, ip: str):
    """Met à jour l'entrée de façon asynchrone pour ne pas bloquer la requête."""

    def worker():
        try:
            data = lookup_location(ip)
            if not data:
                return
            LoginHistory.objects.filter(pk=entry_id).update(
                country=data.get("country", ""),
                region=data.get("region", ""),
                city=data.get("city", ""),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                location_raw=data.get("raw", {}),
            )
        except Exception:
            logger.exception("Erreur lors de la mise à jour de la géolocalisation")

    threading.Thread(target=worker, daemon=True).start()


def _fingerprint_filter(qs, *, user, actor_type, actor_id):
    if user is not None:
        return qs.filter(user=user)
    if actor_type and actor_id is not None:
        return qs.filter(actor_type=actor_type, actor_id=actor_id)
    return qs.none()


def record_login(
    request,
    *,
    actor_type,
    user=None,
    actor_id=None,
    actor_identifier="",
    actor_display="",
    channel="web",
    status=LoginHistory.STATUS_SUCCESS,
    failure_reason="",
    session_key="",
    extra=None,
):
    """Enregistre une entrée d'historique de connexion (succès ou échec)."""
    try:
        ip = get_client_ip(request)
        ua = (request.META.get("HTTP_USER_AGENT") if request is not None else "") or ""
        parsed = parse_user_agent(ua)
        fingerprint = LoginHistory.compute_fingerprint(
            user_agent=ua,
            os_family=parsed["os_family"],
            browser_family=parsed["browser_family"],
            device_family=parsed["device_family"],
        )

        known = False
        if status == LoginHistory.STATUS_SUCCESS and fingerprint:
            qs = LoginHistory.objects.filter(
                device_fingerprint=fingerprint,
                status=LoginHistory.STATUS_SUCCESS,
            )
            known = _fingerprint_filter(
                qs, user=user, actor_type=actor_type, actor_id=actor_id
            ).exists()

        entry = LoginHistory.objects.create(
            user=user,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_identifier=(actor_identifier or "")[:255],
            actor_display=(actor_display or "")[:255],
            channel=channel,
            status=status,
            failure_reason=(failure_reason or "")[:100],
            ip_address=ip,
            user_agent=ua,
            device_label=build_device_label(parsed),
            device_fingerprint=fingerprint,
            session_key=(session_key or "")[:40],
            is_known_device=known,
            extra=extra or {},
            **parsed,
        )
        if ip:
            _resolve_location_async(entry.pk, ip)
        return entry
    except Exception:
        logger.exception("Impossible d'enregistrer l'historique de connexion")
        return None


def record_logout(*, session_key="", user=None, actor_type="", actor_id=None):
    """Marque comme close la dernière session ouverte correspondante."""
    try:
        qs = LoginHistory.objects.filter(
            status=LoginHistory.STATUS_SUCCESS, logout_at__isnull=True
        )
        if session_key:
            qs = qs.filter(session_key=session_key)
        elif user is not None:
            qs = qs.filter(user=user)
        elif actor_type and actor_id is not None:
            qs = qs.filter(actor_type=actor_type, actor_id=actor_id)
        else:
            return 0
        return qs.order_by("-login_at").update(logout_at=timezone.now())
    except Exception:
        logger.exception("Impossible d'enregistrer la déconnexion")
        return 0


def is_known_device(*, request, user=None, actor_type="", actor_id=None) -> bool:
    """Indique si l'appareil utilisé a déjà été utilisé avec succès par l'acteur.

    À utiliser plus tard pour déclencher la double authentification lorsque le
    résultat est ``False``.
    """
    if request is None:
        return False
    ua = request.META.get("HTTP_USER_AGENT", "") or ""
    parsed = parse_user_agent(ua)
    fingerprint = LoginHistory.compute_fingerprint(
        user_agent=ua,
        os_family=parsed["os_family"],
        browser_family=parsed["browser_family"],
        device_family=parsed["device_family"],
    )
    if not fingerprint:
        return False
    qs = LoginHistory.objects.filter(
        device_fingerprint=fingerprint,
        status=LoginHistory.STATUS_SUCCESS,
    )
    return _fingerprint_filter(
        qs, user=user, actor_type=actor_type, actor_id=actor_id
    ).exists()
