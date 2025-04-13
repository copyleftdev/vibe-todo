import json
import time

from todo.validation import (
    generate_task_id,
    validate_boolean,
    validate_task_id,
    validate_title,
)


def log_operation(operation, duration_ms, success, error=None, record_count=1):
    """Log a database operation with performance metrics"""
    # SLA threshold defined as constant
    sla_threshold_ms = 10  # Use lowercase for variable names
    log_entry = {
        "operation": operation,
        "duration_ms": duration_ms,
        "success": success,
        "record_count": record_count,
        "sla_pass": duration_ms <= sla_threshold_ms,  # SLA threshold
        "timestamp": time.time()
    }
    
    if error:
        log_entry["error"] = str(error)
    
    print(json.dumps(log_entry))
    return log_entry

def execute_transaction(conn, operation_name, operation_func, *args, **kwargs):
    """
    Execute a database operation within a transaction with proper error 
    handling and logging.
    
    Args:
        conn: SQLite connection object
        operation_name: Name of the operation for logging
        operation_func: Function to execute inside the transaction
        *args, **kwargs: Arguments to pass to the operation function
        
    Returns:
        Tuple containing (result, success, error)
        where result is the function's return value,
        success is a boolean indicating success/failure,
        and error is None or the exception on failure
        
    Raises:
        Exception: Re-raises any exception from the operation for proper error handling
    """
    start_time = time.time()
    success = False
    error = None
    result = None
    
    try:
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        # Execute the operation
        result = operation_func(*args, **kwargs)
        
        # Commit if successful
        conn.commit()
        success = True
        
    except Exception as e:
        # Handle transaction failure
        try:
            conn.rollback()
        except Exception as rollback_error:  # Use specific exception type
            # Log rollback error
            log_operation(
                f"{operation_name}_rollback_error", 
                0, 
                False, 
                error=str(rollback_error)
            )
        
        error = e
        
        # Log the operation before re-raising
        duration_ms = round((time.time() - start_time) * 1000, 2)
        log_operation(operation_name, duration_ms, False, error)
        
        # Re-raise the exception for proper error handling
        raise
    
    finally:
        # Only log successful operations here since failed ones are logged before re-raising
        if success:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            log_operation(operation_name, duration_ms, success)
    
    return result, success, error

def add_task(conn, title):
    """
    Add a new task with the given title.
    
    Args:
        conn: SQLite connection object
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
    
    result, _, _ = execute_transaction(conn, "add_task", _add_task_impl, title)
    return result

def toggle_done(conn, task_id):
    """
    Toggle the done status of a task.
    
    Args:
        conn: SQLite connection object
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
    
    result, _, _ = execute_transaction(conn, "toggle_done", _toggle_done_impl, task_id)
    return result

def delete_task(conn, task_id):
    """
    Delete a task.
    
    Args:
        conn: SQLite connection object
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
    
    result, _, _ = execute_transaction(conn, "delete_task", _delete_task_impl, task_id)
    return result

def list_tasks(conn, done=None):
    """
    List tasks, optionally filtered by done status.
    
    Args:
        conn: SQLite connection object
        done (bool, optional): Filter by done status. If None, returns all tasks.
        
    Returns:
        list: List of task objects
        
    Raises:
        ValidationError: If done parameter is invalid
        sqlite3.Error: If database operation fails
    """
    def _list_tasks_impl(done):
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
        return results
    
    result, _, _ = execute_transaction(conn, "list_tasks", _list_tasks_impl, done)
    return result

def get_task(conn, task_id):
    """
    Get a task by ID
    
    Args:
        conn: SQLite connection
        task_id: ID of the task to retrieve
        
    Returns:
        Task dictionary or None if not found
    """
    def _get_task():
        # Validate the task ID
        validated_id = validate_task_id(task_id)
        
        # Query the task
        cursor = conn.execute(
            'SELECT id, title, done FROM tasks WHERE id = ?', 
            (validated_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'title': row[1], 
                'done': bool(row[2])
            }
        return None
    
    # Execute within a transaction
    result, _, _ = execute_transaction(conn, "get_task", _get_task)
    return result
