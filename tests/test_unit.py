from todo.models import init_db
from todo.controller import add_task, toggle_done, delete_task, list_tasks

def test_add_and_list():
    conn = init_db()
    task = add_task(conn, "Write blog")
    tasks = list_tasks(conn)
    assert task['title'] == "Write blog"
    assert tasks[0]['done'] is False

def test_toggle():
    conn = init_db()
    task = add_task(conn, "Toggle test")
    success = toggle_done(conn, task['id'])
    assert success
    toggled = list_tasks(conn)[0]
    assert toggled['done'] is True

def test_delete():
    conn = init_db()
    task = add_task(conn, "Delete me")
    delete_task(conn, task['id'])
    tasks = list_tasks(conn)
    assert len(tasks) == 0
