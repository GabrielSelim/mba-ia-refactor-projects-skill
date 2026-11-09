"""Casos de uso de categorias (antes misturados ao blueprint de relatórios)."""
from sqlalchemy import func

from controllers.validators import require_json
from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from utils.helpers import DEFAULT_COLOR, is_valid_color


def _get_or_404(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def _validate_color(color):
    if not is_valid_color(color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


def list_categories():
    rows = (db.session.query(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id).all())
    result = []
    for category, task_count in rows:
        data = category.to_dict()
        data['task_count'] = task_count
        result.append(data)
    return result


def create_category(data):
    data = require_json(data)
    if not data.get('name'):
        raise ValidationError('Nome é obrigatório')
    category = Category()
    category.name = data['name']
    category.description = data.get('description', '')
    category.color = _validate_color(data.get('color', DEFAULT_COLOR))
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(category_id, data):
    category = _get_or_404(category_id)
    data = require_json(data)
    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = _validate_color(data['color'])
    db.session.commit()
    return category.to_dict()


def delete_category(category_id):
    category = _get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return {'message': 'Categoria deletada'}
