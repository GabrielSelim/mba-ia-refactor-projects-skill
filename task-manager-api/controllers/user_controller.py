"""Casos de uso de usuários e autenticação."""
import logging

from sqlalchemy import func

from controllers.validators import require_json
from database import db
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.task import Task
from models.user import User
from services.auth_service import issue_token
from utils.helpers import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, VALID_ROLES, utc_now, validate_email

logger = logging.getLogger(__name__)


def get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def _ensure_email_free(email, ignore_user_id=None):
    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != ignore_user_id:
        raise ConflictError('Email já cadastrado')


def list_users():
    rows = (db.session.query(User, func.count(Task.id))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id).all())
    result = []
    for user, task_count in rows:
        data = user.to_dict()
        data['task_count'] = task_count
        result.append(data)
    return result


def get_user(user_id):
    user = get_user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(data):
    data = require_json(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    role = data.get('role', DEFAULT_ROLE)
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not validate_email(email):
        raise ValidationError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    _ensure_email_free(email)
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')

    user = User()
    user.name, user.email, user.role = name, email, role
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info('usuario_criado id=%s', user.id)
    return user.to_dict()


def update_user(user_id, data):
    user = get_user_or_404(user_id)
    data = require_json(data)
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if not validate_email(data['email']):
            raise ValidationError('Email inválido')
        _ensure_email_free(data['email'], ignore_user_id=user_id)
        user.email = data['email']
    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])
    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            raise ValidationError('Role inválido')
        user.role = data['role']
    if 'active' in data:
        user.active = data['active']
    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = get_user_or_404(user_id)
    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    logger.info('usuario_deletado id=%s', user_id)
    return {'message': 'Usuário deletado com sucesso'}


def get_user_tasks(user_id):
    get_user_or_404(user_id)
    now = utc_now()
    return [{
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'status': t.status,
        'priority': t.priority,
        'created_at': str(t.created_at),
        'due_date': str(t.due_date) if t.due_date else None,
        'overdue': t.is_overdue(now),
    } for t in Task.query.filter_by(user_id=user_id).all()]


def login(data):
    data = require_json(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    db.session.commit()   # persiste a migração de hash legado, se houve
    return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': issue_token(user)}
