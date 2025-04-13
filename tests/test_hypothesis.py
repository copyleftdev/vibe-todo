from hypothesis import given
from hypothesis.strategies import text

from todo.controller import add_task, delete_task, list_tasks, toggle_done
from todo.models import init_db


@given(title=text(min_size=1, max_size=100))
def test_add_task_persists(title):
    conn = init_db()
    task = add_task(conn, title)
    tasks = list_tasks(conn)
    assert any(t['id'] == task['id'] for t in tasks)

@given(title=text(min_size=1, max_size=100))
def test_toggle_is_effective(title):
    conn = init_db()
    task = add_task(conn, title)
    toggle_done(conn, task['id'])
    tasks = list_tasks(conn)
    assert tasks[0]['done'] is True
    toggle_done(conn, task['id'])
    tasks = list_tasks(conn)
    assert tasks[0]['done'] is False

@given(title=text(min_size=1, max_size=100))
def test_delete_removes_task(title):
    conn = init_db()
    task = add_task(conn, title)
    delete_task(conn, task['id'])
    tasks = list_tasks(conn)
    assert all(t['id'] != task['id'] for t in tasks)
