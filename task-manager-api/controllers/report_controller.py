"""Relatórios: agregações no banco no lugar de loops com uma query por entidade."""
from datetime import timedelta

from sqlalchemy import case, func

from controllers.task_controller import overdue_tasks, status_counts
from controllers.user_controller import get_user_or_404
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import HIGH_PRIORITY_MAX, calculate_percentage, utc_now

RECENT_DAYS = 7
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def summary_report():
    now = utc_now()
    by_status = status_counts()
    by_priority = dict(db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all())

    overdue = overdue_tasks(now)
    since = now - timedelta(days=RECENT_DAYS)
    recent_created = Task.query.filter(Task.created_at >= since).count()
    recent_done = Task.query.filter(Task.status == 'done', Task.updated_at >= since).count()

    productivity = (db.session.query(User.id, User.name, func.count(Task.id),
                                     func.sum(case((Task.status == 'done', 1), else_=0)))
                    .outerjoin(Task, Task.user_id == User.id)
                    .group_by(User.id).all())

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': sum(by_status.values()),
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
        },
        'tasks_by_status': {s: by_status.get(s, 0) for s in ('pending', 'in_progress', 'done', 'cancelled')},
        'tasks_by_priority': {label: by_priority.get(p, 0) for p, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue),
            'tasks': [{'id': t.id, 'title': t.title, 'due_date': str(t.due_date),
                       'days_overdue': (now - t.due_date).days} for t in overdue],
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_created,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': [{
            'user_id': uid,
            'user_name': name,
            'total_tasks': total,
            'completed_tasks': completed or 0,
            'completion_rate': calculate_percentage(completed or 0, total),
        } for uid, name, total, completed in productivity],
    }


def user_report(user_id):
    user = get_user_or_404(user_id)
    now = utc_now()
    tasks = Task.query.filter_by(user_id=user_id).all()
    counts = {s: 0 for s in ('done', 'pending', 'in_progress', 'cancelled')}
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
    total = len(tasks)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **counts,
            'overdue': sum(1 for t in tasks if t.is_overdue(now)),
            'high_priority': sum(1 for t in tasks if t.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': calculate_percentage(counts['done'], total),
        },
    }
