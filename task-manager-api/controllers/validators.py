"""Validação de entrada compartilhada pelos controllers (lança ValidationError → 400)."""
from errors import ValidationError
from utils.helpers import MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH, VALID_STATUSES, parse_date


def require_json(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')
    return data


def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título deve ser texto')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return status


def validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValidationError('Prioridade inválida')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return priority


def validate_due_date(value, message):
    parsed = parse_date(value)
    if parsed is None:
        raise ValidationError(message)
    return parsed


def normalize_tags(tags):
    return ','.join(tags) if isinstance(tags, list) else tags


def optional_int(value, field):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError(f'{field} inválido') from exc
