"""Imprime os valores agregados (sem timestamps) para comparar original x refatorado."""
import json
import sys
import urllib.request

BASE = sys.argv[1].rstrip("/")


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as resp:
        return json.loads(resp.read())


summary = get("/reports/summary")
summary.pop("generated_at")
for task in summary["overdue"]["tasks"]:
    task.pop("due_date")
users = [{k: v for k, v in u.items() if k != "created_at"} for u in get("/users")]
categories = [{k: v for k, v in c.items() if k != "created_at"} for c in get("/categories")]
tasks = [{k: t[k] for k in ("id", "overdue", "user_name", "category_name", "status")} for t in get("/tasks")]
print(json.dumps({
    "stats": get("/tasks/stats"),
    "summary": summary,
    "user_report_1": get("/reports/user/1"),
    "users": users,
    "categories": categories,
    "tasks": tasks,
}, sort_keys=True, ensure_ascii=False))
