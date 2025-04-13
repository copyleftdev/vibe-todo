import uuid
import sqlite3
import time
import json
import logging
from todo.validation import validate_title, validate_task_id, validate_boolean, generate_task_id, ValidationError

def log_operation(operation, duration_ms, success, error=None, record_count=1):
    """Log operation details in structured JSON format."""
    log_data = {
        "operation": operation,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "record_count": record_count,
        "sla_pass": duration_ms <= 10,  # 10ms SLA threshold
        "timestamp": time.time()
    }
    
    if error:
        log_data["error"] = str(error)
        
    print(json.dumps(log_data))
    return log_data

def execute_transaction(conn, operation_name, operation_func, *args, **kwargs):
    """
    Execute a database operation within a transaction with proper error handling and logging.
    
    Args:
        conn: Database connection
        operation_name: Name of the operation for logging
        operation_func: Function to execute within the transaction
        *args, **kwargs: Arguments to pass to the operation function
        
    Returns:
        Result of the operation function
    """
    start_time = time.time()
    success = False
    error = None
    result = None
    
    try:
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Execute the operation
        result = operation_func(*args, **kwargs)
        
        # Commit the transaction
        conn.commit()
        success = True
        
    except Exception as e:
        # Rollback on error
        try:
            conn.rollback()
        except:
            pass  # Ignore rollback errors
            
        error = e
        raise
        
    finally:
        # Calculate duration and log the operation
        duration_ms = (time.time() - start_time) * 1000
        log_operation(operation_name, duration_ms, success, error)
        
    return result

def add_task(conn, title):
    """
    Add a new task with the given title.
    
    Args:
        conn: Database connection
        title (str): Title of the task
    
    Returns:
        dict: The created task object
        
    Raises:
        ValidationError: If title is invalid
        sqlite3.Error: If database operation fails
    """
    def _add_task_impl(title):
        # Validate and sanitize title
        sanitized_title = validate_title(title)
        
        # Generate a task ID
        task_id = generate_task_id()
        
        # Insert the task
        conn.execute('INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)', 
                     (task_id, sanitized_title, 0))
        
        return {'id': task_id, 'title': sanitized_title, 'done': False}
    
    return execute_transaction(conn, "add_task", _add_task_impl, title)

def toggle_done(conn, task_id):
    """
    Toggle the done status of a task.
    
    Args:
        conn: Database connection
        task_id (str): ID of the task to toggle
        
    Returns:
        bool: True if task was toggled, False if task doesn't exist
        
    Raises:
        ValidationError: If task_id is invalid
        sqlite3.Error: If database operation fails
    """
    def _toggle_done_impl(task_id):
        # Validate task ID
        validated_id = validate_task_id(task_id)
        
        # Get current status
        cursor = conn.execute('SELECT done FROM tasks WHERE id = ?', (validated_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
            
        # Toggle status
        new_done = 0 if row[0] else 1
        conn.execute('UPDATE tasks SET done = ? WHERE id = ?', (new_done, validated_id))
        
        return True
    
    return execute_transaction(conn, "toggle_done", _toggle_done_impl, task_id)

def delete_task(conn, task_id):
    """
    Delete a task.
    
    Args:
        conn: Database connection
        task_id (str): ID of the task to delete
        
    Returns:
        bool: True if task was deleted, False if task doesn't exist
        
    Raises:
        ValidationError: If task_id is invalid
        sqlite3.Error: If database operation fails
    """
    def _delete_task_impl(task_id):
        # Validate task ID
        validated_id = validate_task_id(task_id)
        
        # Check if task exists
        cursor = conn.execute('SELECT id FROM tasks WHERE id = ?', (validated_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
            
        # Delete the task
        conn.execute('DELETE FROM tasks WHERE id = ?', (validated_id,))
        
        return True
    
    return execute_transaction(conn, "delete_task", _delete_task_impl, task_id)

def list_tasks(conn, done=None):
    """
    List tasks, optionally filtered by done status.
    
    Args:
        conn: Database connection
        done (bool, optional): Filter by done status. If None, returns all tasks.
        
    Returns:
        list: List of task objects
        
    Raises:
        ValidationError: If done parameter is invalid
        sqlite3.Error: If database operation fails
    """
    start_time = time.time()
    success = False
    error = None
    results = []
    
    try:
        # Validate done parameter if provided
        done_filter = None if done is None else validate_boolean(done)
        
        # Query tasks
        if done_filter is None:
            cursor = conn.execute('SELECT id, title, done FROM tasks')
        else:
            cursor = conn.execute('SELECT id, title, done FROM tasks WHERE done = ?', 
                                 (int(done_filter),))
        
        # Convert to list of dicts
        results = [{'id': row[0], 'title': row[1], 'done': bool(row[2])} 
                  for row in cursor.fetchall()]
        success = True
        
    except Exception as e:
        error = e
        raise
        
    finally:
        # Calculate duration and log
        duration_ms = (time.time() - start_time) * 1000
        log_operation("list_tasks", duration_ms, success, error, len(results))
    
    return results

def get_task(conn, task_id):
    """
    Get a single task by ID.
    
    Args:
        conn: Database connection
        task_id (str): ID of the task to get
        
    Returns:
        dict: Task object or None if not found
        
    Raises:
        ValidationError: If task_id is invalid
        sqlite3.Error: If database operation fails
    """
    start_time = time.time()
    success = False
    error = None
    result = None
    
    try:
        # Validate task ID
        validated_id = validate_task_id(task_id)
        
        # Query the task
        cursor = conn.execute('SELECT id, title, done FROM tasks WHERE id = ?', (validated_id,))
        row = cursor.fetchone()
        
        if row:
            result = {'id': row[0], 'title': row[1], 'done': bool(row[2])}
        success = True
        
    except Exception as e:
        error = e
        raise
        
    finally:
        # Calculate duration and log
        duration_ms = (time.time() - start_time) * 1000
        log_operation("get_task", duration_ms, success, error)
    
    return result
