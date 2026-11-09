"""Helpers puros e constantes de domínio compartilhadas."""
import re
from datetime import datetime, timezone

VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
FINAL_STATUSES = ("done", "cancelled")
VALID_ROLES = ("user", "admin", "manager")
ROLE_ADMIN = "admin"
DEFAULT_ROLE = "user"
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2
DEFAULT_STATUS = "pending"
DEFAULT_COLOR = "#000000"
DATE_FORMAT = "%Y-%m-%d"

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def utc_now():
    """UTC sem tzinfo, compatível com os datetimes já gravados no SQLite (substitui datetime.utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    return round((part / total) * 100, 2) if total else 0


def validate_email(email):
    return isinstance(email, str) and bool(_EMAIL_RE.match(email))


def is_valid_color(color):
    return isinstance(color, str) and bool(_COLOR_RE.match(color))


def parse_date(value):
    """Data no formato YYYY-MM-DD; None se inválida."""
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        return None
