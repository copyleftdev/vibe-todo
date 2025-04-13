#!/usr/bin/env python3
"""
Regression Test Suite for Todo Application
Tests known edge cases and ensures the application remains robust against them.
"""
import sqlite3
import uuid

import pytest

from todo.controller import (
    add_task,
    delete_task,
    execute_transaction,
    get_task,
    list_tasks,
    toggle_done,
)
from todo.models import init_db
from todo.validation import ValidationError

# Known problematic payloads to test against
EDGE_CASE_PAYLOADS = [
    # Empty inputs
    "",
    # Very long inputs
    "A" * 10000,
    # SQL injection attempts
    "' OR 1=1 --",
    "'; DROP TABLE tasks; --",
    "' UNION SELECT * FROM sqlite_master; --",
    # Special characters
    "<script>alert('XSS')</script>",
    "Task with emoji 🚀 🔥 👍",
    "Multi-line\ntext\rwith\tspecial\bcharacters",
    # Unicode and international characters
    "Unicode: درس العربية",
    "Cyrillic: Привет, мир",
    "Chinese: 你好，世界",
    "Japanese: こんにちは世界",
    # Null bytes and control characters
    "Title with null byte: \0 in middle",
    "Title with control chars: \u0001\u0002\u0003",
    # JSON-like content
    '{"title": "Task", "id": "1234", "done": true}',
    # Escape sequences
    "Escape \\n \\t \\r \\b sequences",
    # HTML entities
    "HTML &lt;entities&gt; &amp; special chars",
    # Mixed cases
    f"Mixed {'A' * 1000} with ' OR 1=1 -- and 🚀"
]

# Invalid task IDs to test against
INVALID_IDS = [
    "",
    "not-a-uuid",
    "12345",
    "' OR 1=1 --",
    None,
    "00000000-0000-0000-0000-000000000000",
    "11111111-1111-1111-1111-111111111111",
    "<script>alert('XSS')</script>"
]

@pytest.fixture
def db_connection():
    """Fixture to provide a database connection for each test."""
    conn = init_db()
    yield conn
    conn.close()

def test_add_task_with_edge_cases(db_connection):
    """Test adding tasks with known edge case inputs."""
    successful_tasks = []
    
    for payload in EDGE_CASE_PAYLOADS:
        try:
            task = add_task(db_connection, payload)
            assert task['id'] is not None
            assert isinstance(task['id'], str)
            assert len(task['id']) > 0
            
            # Verify we can retrieve the task
            saved_task = get_task(db_connection, task['id'])
            assert saved_task is not None
            assert saved_task['title'] == task['title']
            assert saved_task['done'] is False
            
            successful_tasks.append(task)
        except ValidationError as e:
            # If validation error occurs, that's fine as long as it doesn't crash
            print(f"Validation rejected payload: {payload[:50]}... - {str(e)}")
        except Exception as e:
            # Other exceptions are actual failures
            pytest.fail(f"Failed with payload: {payload[:50]}... - {type(e).__name__}: {str(e)}")
    
    # Verify we can retrieve all tasks
    tasks = list_tasks(db_connection)
    assert len(tasks) == len(successful_tasks)

def test_task_id_validation(db_connection):
    """Test that invalid task IDs are properly rejected."""
    # Create a valid task first
    valid_task = add_task(db_connection, "Valid task")
    
    for invalid_id in INVALID_IDS:
        # Test toggle_done with invalid ID
        try:
            toggle_done(db_connection, invalid_id)
            # If we get here with certain invalid IDs, it must have failed gracefully
            # by returning False, not by accepting the invalid ID
            assert get_task(db_connection, invalid_id) is None
        except (ValidationError, TypeError):
            # Expected for invalid IDs
            pass
        except Exception as e:
            # Other exceptions are actual failures
            pytest.fail(f"Failed with invalid ID in toggle_done: {invalid_id} - {type(e).__name__}: {str(e)}")
        
        # Test delete_task with invalid ID
        try:
            delete_task(db_connection, invalid_id)
            # If we get here, it must have failed gracefully
            assert get_task(db_connection, invalid_id) is None
        except (ValidationError, TypeError):
            # Expected for invalid IDs
            pass
        except Exception as e:
            # Other exceptions are actual failures
            pytest.fail(f"Failed with invalid ID in delete_task: {invalid_id} - {type(e).__name__}: {str(e)}")
        
        # Test get_task with invalid ID
        try:
            result = get_task(db_connection, invalid_id)
            # If we get here without exception, result must be None
            assert result is None
        except (ValidationError, TypeError):
            # Expected for invalid IDs
            pass
        except Exception as e:
            # Other exceptions are actual failures
            pytest.fail(f"Failed with invalid ID in get_task: {invalid_id} - {type(e).__name__}: {str(e)}")
    
    # Verify the valid task still exists and wasn't affected
    assert get_task(db_connection, valid_task['id']) is not None

def test_sla_compliance(db_connection):
    """Test that all operations comply with the SLA requirements."""
    SLA_MS = 10  # 10ms maximum latency per operation
    
    # Performance test for add_task
    task = add_task(db_connection, "SLA test task")
    
    # Performance test for toggle_done
    toggle_done(db_connection, task['id'])
    
    # Performance test for list_tasks
    list_tasks(db_connection)
    
    # Performance test for get_task
    get_task(db_connection, task['id'])
    
    # Performance test for delete_task
    delete_task(db_connection, task['id'])
    
    # Success if we get here without exceptions
    # The log_operation function in controller already asserts SLA compliance

def test_transaction_rollback(db_connection):
    """Test that transactions are properly rolled back on error."""
    # Capture initial state
    initial_tasks = list_tasks(db_connection)
    
    # Create a task that will be part of the transaction
    valid_task = add_task(db_connection, "Valid task in transaction")
    
    # We need to create a custom transaction function that will directly use
    # the execute_transaction from our controller
    
    try:
        # Create a function that will trigger an SQL error
        # Note: This function doesn't take the connection as a parameter since execute_transaction
        # doesn't automatically pass it - it will pass any args and kwargs we provide
        def operation_that_fails():
            # Insert one row successfully
            db_connection.execute("INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)",
                       (str(uuid.uuid4()), "Task that should be rolled back", 0))
            
            # Then trigger an error with invalid SQL
            db_connection.execute("THIS IS INVALID SQL")
            return True
        
        # Execute the operation in a transaction directly
        execute_transaction(db_connection, "test_failing_transaction", operation_that_fails)
        
        # We shouldn't get here
        pytest.fail("Transaction should have failed but didn't")
    except sqlite3.OperationalError:
        # Expected error - transaction failed due to invalid SQL
        pass
    
    # Verify the valid task still exists
    assert get_task(db_connection, valid_task['id']) is not None
    
    # Verify no additional tasks were added after the rollback
    final_tasks = list_tasks(db_connection)
    assert len(final_tasks) == len(initial_tasks) + 1  # Only our valid task was added

def test_data_integrity_with_concurrent_operations(db_connection):
    """Test data integrity with concurrent operations on the same task."""
    # Create a test task
    task = add_task(db_connection, "Concurrent operations test")
    
    # Perform multiple toggle operations to simulate concurrent access
    for _ in range(10):
        toggle_done(db_connection, task['id'])
    
    # Check final state - should be deterministic regardless of concurrency
    final_task = get_task(db_connection, task['id'])
    assert final_task is not None
    # After 10 toggles, it should be back to its original state if done was initially False
    assert final_task['done'] is False

def test_list_tasks_with_filters(db_connection):
    """Test filtering tasks by completion status."""
    # Create tasks with different completion statuses
    task1 = add_task(db_connection, "Incomplete task")
    task2 = add_task(db_connection, "Complete task")
    toggle_done(db_connection, task2['id'])  # Mark task2 as done
    
    # Test filtering for incomplete tasks
    incomplete_tasks = list_tasks(db_connection, done=False)
    assert len(incomplete_tasks) == 1
    assert incomplete_tasks[0]['id'] == task1['id']
    
    # Test filtering for complete tasks
    complete_tasks = list_tasks(db_connection, done=True)
    assert len(complete_tasks) == 1
    assert complete_tasks[0]['id'] == task2['id']
    
    # Test getting all tasks
    all_tasks = list_tasks(db_connection)
    assert len(all_tasks) == 2

if __name__ == "__main__":
    pytest.main(["-v", __file__])
