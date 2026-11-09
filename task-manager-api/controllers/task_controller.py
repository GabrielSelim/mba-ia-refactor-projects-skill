"""Casos de uso de tasks (regra que antes vivia em routes/task_routes.py)."""
import logging

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from controllers.validators import (normalize_tags, optional_int, require_json, validate_due_date,
                                    validate_priority, validate_status, validate_title)
from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import DEFAULT_PRIORITY, DEFAULT_STATUS, FINAL_STATUSES, calculate_percentage, utc_now

logger = logging.getLogger(__name__)


def get_task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_user(user_id):
    if user_id and db.session.get(User, user_id) is None:
        raise NotFoundError('Usuário não encontrado')


def _ensure_category(category_id):
    if category_id and db.session.get(Category, category_id) is None:
        raise NotFoundError('Categoria não encontrada')


def list_tasks():
    now = utc_now()
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    result = []
    for task in tasks:
        data = task.to_dict()
        data['overdue'] = task.is_overdue(now)
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result


def get_task(task_id):
    task = get_task_or_404(task_id)
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def create_task(data):
    data = require_json(data)
    if not data.get('title'):
        raise ValidationError('Título é obrigatório')

    task = Task()
    task.title = validate_title(data['title'])
    task.description = data.get('description', '')
    task.status = validate_status(data.get('status', DEFAULT_STATUS))
    task.priority = validate_priority(data.get('priority', DEFAULT_PRIORITY))
    task.user_id = data.get('user_id')
    task.category_id = data.get('category_id')
    _ensure_user(task.user_id)
    _ensure_category(task.category_id)
    if data.get('due_date'):
        task.due_date = validate_due_date(data['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
    if data.get('tags'):
        task.tags = normalize_tags(data['tags'])

    db.session.add(task)
    db.session.commit()
    logger.info('task_criada id=%s', task.id)
    return task.to_dict()


def update_task(task_id, data):
    task = get_task_or_404(task_id)
    data = require_json(data)

    if 'title' in data:
        task.title = validate_title(data['title'])
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = validate_status(data['status'])
    if 'priority' in data:
        task.priority = validate_priority(data['priority'])
    if 'user_id' in data:
        _ensure_user(data['user_id'])
        task.user_id = data['user_id']
    if 'category_id' in data:
        _ensure_category(data['category_id'])
        task.category_id = data['category_id']
    if 'due_date' in data:
        task.due_date = validate_due_date(data['due_date'], 'Formato de data inválido') if data['due_date'] else None
    if 'tags' in data:
        task.tags = normalize_tags(data['tags'])

    task.updated_at = utc_now()
    db.session.commit()
    logger.info('task_atualizada id=%s', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = get_task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    logger.info('task_deletada id=%s', task_id)
    return {'message': 'Task deletada com sucesso'}


def search_tasks(args):
    query = Task.query
    term = args.get('q', '')
    if term:
        query = query.filter(db.or_(Task.title.like(f'%{term}%'), Task.description.like(f'%{term}%')))
    if args.get('status'):
        query = query.filter(Task.status == args['status'])
    priority = optional_int(args.get('priority'), 'priority')
    if priority is not None:
        query = query.filter(Task.priority == priority)
    user_id = optional_int(args.get('user_id'), 'user_id')
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    return [t.to_dict() for t in query.all()]


def status_counts():
    return dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())


def overdue_tasks(now=None):
    now = now or utc_now()
    return Task.query.filter(Task.due_date.isnot(None), Task.due_date < now,
                             Task.status.notin_(FINAL_STATUSES)).all()


def task_stats():
    counts = status_counts()
    total = sum(counts.values())
    done = counts.get('done', 0)
    return {
        'total': total,
        'pending': counts.get('pending', 0),
        'in_progress': counts.get('in_progress', 0),
        'done': done,
        'cancelled': counts.get('cancelled', 0),
        'overdue': len(overdue_tasks()),
        'completion_rate': calculate_percentage(done, total),
    }
