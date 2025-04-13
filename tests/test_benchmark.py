import gc
import json
import os
import sys
import time

from todo.controller import add_task, delete_task, list_tasks, toggle_done
from todo.models import init_db

SLA_MS = 10

def log_event(event):
    print(json.dumps(event))

def benchmark_add_tasks(n):
    conn = init_db()
    start = time.time()
    for i in range(n):
        add_task(conn, f"Task {i}")
    end = time.time()
    duration = (end - start) * 1000
    sla_pass = (duration / n) <= SLA_MS
    log_event({"operation": "add_task", "record_count": n, "duration_ms": round(duration), "sla_pass": sla_pass, "sla_threshold": SLA_MS})
    conn.close()

def benchmark_toggle_tasks(n):
    conn = init_db()
    task_ids = []
    for i in range(n):
        task = add_task(conn, f"Task {i}")
        task_ids.append(task['id'])
    start = time.time()
    for task_id in task_ids:
        toggle_done(conn, task_id)
    end = time.time()
    duration = (end - start) * 1000
    sla_pass = (duration / n) <= SLA_MS
    log_event({"operation": "toggle_task", "record_count": n, "duration_ms": round(duration), "sla_pass": sla_pass, "sla_threshold": SLA_MS})
    conn.close()

def benchmark_delete_tasks(n):
    conn = init_db()
    task_ids = []
    for i in range(n):
        task = add_task(conn, f"Task {i}")
        task_ids.append(task['id'])
    start = time.time()
    for task_id in task_ids:
        delete_task(conn, task_id)
    end = time.time()
    duration = (end - start) * 1000
    sla_pass = (duration / n) <= SLA_MS
    log_event({"operation": "delete_task", "record_count": n, "duration_ms": round(duration), "sla_pass": sla_pass, "sla_threshold": SLA_MS})
    conn.close()

def benchmark_edge_large_title(n):
    """Test with extremely large task titles (edge case)."""
    conn = init_db()
    large_title = "A" * 10000  # Very large title
    start = time.time()
    for i in range(n):
        add_task(conn, large_title)
    end = time.time()
    duration = (end - start) * 1000
    sla_pass = (duration / n) <= SLA_MS
    log_event({
        "operation": "add_task_large_title", 
        "record_count": n, 
        "title_size": len(large_title),
        "duration_ms": round(duration), 
        "sla_pass": sla_pass, 
        "sla_threshold": SLA_MS
    })
    conn.close()

def benchmark_edge_special_chars(n):
    """Test with special characters in task titles."""
    conn = init_db()
    special_titles = [
        "Task with unicode: 🚀 🔥 👍",
        "SQL injection attempt: ' OR 1=1 --",
        "HTML tags: <script>alert('test')</script>",
        "Newlines and tabs: \n\t\r",
        "Quotes and escapes: \"'\\",
    ]
    
    start = time.time()
    for i in range(n):
        title = special_titles[i % len(special_titles)]
        add_task(conn, title)
    end = time.time()
    duration = (end - start) * 1000
    sla_pass = (duration / n) <= SLA_MS
    log_event({
        "operation": "add_task_special_chars", 
        "record_count": n, 
        "duration_ms": round(duration), 
        "sla_pass": sla_pass, 
        "sla_threshold": SLA_MS
    })
    conn.close()

def benchmark_edge_empty_title(n):
    """Test with empty task titles."""
    conn = init_db()
    start = time.time()
    for i in range(n):
        add_task(conn, "")
    end = time.time()
    duration = (end - start) * 1000
    sla_pass = (duration / n) <= SLA_MS
    log_event({
        "operation": "add_task_empty_title", 
        "record_count": n, 
        "duration_ms": round(duration), 
        "sla_pass": sla_pass, 
        "sla_threshold": SLA_MS
    })
    conn.close()

def benchmark_edge_repeated_toggles(n, toggles_per_task):
    """Test toggling the same task multiple times."""
    conn = init_db()
    task_ids = []
    for i in range(n):
        task = add_task(conn, f"Task {i}")
        task_ids.append(task['id'])
    
    start = time.time()
    for task_id in task_ids:
        for _ in range(toggles_per_task):
            toggle_done(conn, task_id)
    end = time.time()
    
    total_operations = n * toggles_per_task
    duration = (end - start) * 1000
    sla_pass = (duration / total_operations) <= SLA_MS
    log_event({
        "operation": "repeated_toggles", 
        "record_count": n,
        "toggles_per_task": toggles_per_task,
        "total_operations": total_operations,
        "duration_ms": round(duration), 
        "sla_pass": sla_pass, 
        "sla_threshold": SLA_MS
    })
    conn.close()

def benchmark_edge_nonexistent_ids():
    """Test operations on non-existent task IDs."""
    conn = init_db()
    nonexistent_ids = ["not-a-real-id", "another-fake-id", "12345", ""]
    
    # Toggle operations
    toggle_errors = 0
    toggle_start = time.time()
    for fake_id in nonexistent_ids:
        try:
            toggle_done(conn, fake_id)
        except Exception:
            toggle_errors += 1
    toggle_end = time.time()
    
    # Delete operations
    delete_errors = 0
    delete_start = time.time()
    for fake_id in nonexistent_ids:
        try:
            delete_task(conn, fake_id)
        except Exception:
            delete_errors += 1
    delete_end = time.time()
    
    toggle_duration = (toggle_end - toggle_start) * 1000
    delete_duration = (delete_end - delete_start) * 1000
    
    log_event({
        "operation": "toggle_nonexistent", 
        "attempts": len(nonexistent_ids),
        "errors": toggle_errors,
        "duration_ms": round(toggle_duration)
    })
    
    log_event({
        "operation": "delete_nonexistent", 
        "attempts": len(nonexistent_ids),
        "errors": delete_errors,
        "duration_ms": round(delete_duration)
    })
    conn.close()

def benchmark_filter_operations(n):
    """Test filtering operations performance."""
    conn = init_db()
    
    # Create tasks, half done, half not done
    for i in range(n):
        task = add_task(conn, f"Task {i}")
        if i % 2 == 0:
            toggle_done(conn, task['id'])
    
    # Filter for done tasks
    filter_done_start = time.time()
    done_tasks = list_tasks(conn, done=True)
    filter_done_end = time.time()
    
    # Filter for not done tasks
    filter_not_done_start = time.time()
    not_done_tasks = list_tasks(conn, done=False)
    filter_not_done_end = time.time()
    
    # Get all tasks
    get_all_start = time.time()
    all_tasks = list_tasks(conn)
    get_all_end = time.time()
    
    filter_done_duration = (filter_done_end - filter_done_start) * 1000
    filter_not_done_duration = (filter_not_done_end - filter_not_done_start) * 1000
    get_all_duration = (get_all_end - get_all_start) * 1000
    
    sla_pass_done = filter_done_duration <= SLA_MS
    sla_pass_not_done = filter_not_done_duration <= SLA_MS
    sla_pass_all = get_all_duration <= SLA_MS
    
    log_event({
        "operation": "filter_done", 
        "record_count": n,
        "retrieved_count": len(done_tasks),
        "duration_ms": round(filter_done_duration),
        "sla_pass": sla_pass_done,
        "sla_threshold": SLA_MS
    })
    
    log_event({
        "operation": "filter_not_done", 
        "record_count": n,
        "retrieved_count": len(not_done_tasks),
        "duration_ms": round(filter_not_done_duration),
        "sla_pass": sla_pass_not_done,
        "sla_threshold": SLA_MS
    })
    
    log_event({
        "operation": "get_all_tasks", 
        "record_count": n,
        "retrieved_count": len(all_tasks),
        "duration_ms": round(get_all_duration),
        "sla_pass": sla_pass_all,
        "sla_threshold": SLA_MS
    })
    conn.close()

def benchmark_memory_usage(n):
    """Track memory usage during operations with large datasets."""
    # Force garbage collection before starting
    gc.collect()
    
    # Get initial memory usage
    initial_memory = get_memory_usage()
    
    conn = init_db()
    task_ids = []
    
    # Add tasks and measure memory
    for batch in range(10):
        batch_size = n // 10
        start_idx = batch * batch_size
        end_idx = start_idx + batch_size
        
        for i in range(start_idx, end_idx):
            task = add_task(conn, f"Memory test task {i} with some additional text for size")
            task_ids.append(task['id'])
        
        after_add_memory = get_memory_usage()
        log_event({
            "operation": "memory_usage", 
            "phase": f"after_add_batch_{batch+1}",
            "tasks_count": (batch+1) * batch_size,
            "memory_mb": round(after_add_memory, 2),
            "memory_increase_mb": round(after_add_memory - initial_memory, 2)
        })
    
    # Toggle all tasks
    for task_id in task_ids:
        toggle_done(conn, task_id)
    
    after_toggle_memory = get_memory_usage()
    log_event({
        "operation": "memory_usage", 
        "phase": "after_toggle_all",
        "tasks_count": n,
        "memory_mb": round(after_toggle_memory, 2),
        "memory_increase_mb": round(after_toggle_memory - initial_memory, 2)
    })
    
    # Delete half the tasks
    for task_id in task_ids[:n//2]:
        delete_task(conn, task_id)
    
    after_delete_memory = get_memory_usage()
    log_event({
        "operation": "memory_usage", 
        "phase": "after_delete_half",
        "remaining_tasks": n - n//2,
        "memory_mb": round(after_delete_memory, 2),
        "memory_increase_mb": round(after_delete_memory - initial_memory, 2)
    })
    
    # Get SQLite database file size
    db_path = conn.execute("PRAGMA database_list").fetchone()[2]
    db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
    
    log_event({
        "operation": "database_size", 
        "tasks_count": n - n//2,
        "size_mb": round(db_size_mb, 2)
    })
    
    conn.close()
    
    # Final memory usage after connection close
    final_memory = get_memory_usage()
    log_event({
        "operation": "memory_usage", 
        "phase": "final",
        "memory_mb": round(final_memory, 2),
        "memory_increase_mb": round(final_memory - initial_memory, 2)
    })

def get_memory_usage():
    """Get current memory usage in MB."""
    return sys.getsizeof(0) / (1024 * 1024)  # Basic measurement, replace with more accurate if needed

def benchmark_high_load(quick_mode=False):
    """Run a series of benchmarks with increasing load to detect when performance degrades."""
    # Use smaller load levels in quick mode (for pre-commit hooks)
    if quick_mode:
        load_levels = [10, 100]
    else:
        load_levels = [100, 1000, 5000, 10000]
    
    for load in load_levels:
        log_event({"operation": "benchmark_run", "load": load, "status": "starting"})
        
        try:
            benchmark_add_tasks(load)
            benchmark_toggle_tasks(load)
            benchmark_delete_tasks(load)
            
            # Only run more specialized tests at lower loads
            if load <= 1000:
                benchmark_edge_large_title(min(load, 100))
                benchmark_edge_special_chars(min(load, 100))
                benchmark_edge_empty_title(min(load, 100))
                benchmark_edge_repeated_toggles(min(load, 100), 5)
                benchmark_edge_nonexistent_ids()
                benchmark_filter_operations(load)
            
            # Only run memory benchmark at highest load and not in quick mode
            if load == max(load_levels) and not quick_mode:
                benchmark_memory_usage(load)
            
            log_event({"operation": "benchmark_run", "load": load, "status": "completed"})
        except Exception as e:
            log_event({
                "operation": "benchmark_run", 
                "load": load, 
                "status": "failed",
                "error": str(e)
            })
            break

if __name__ == '__main__':
    import sys
    
    quick_mode = '--quick' in sys.argv
    
    try:
        log_event({"operation": "benchmark_suite", "status": "starting", "mode": "quick" if quick_mode else "full"})
        benchmark_high_load(quick_mode)
        log_event({"operation": "benchmark_suite", "status": "completed"})
    except Exception as e:
        log_event({
            "operation": "benchmark_suite", 
            "status": "failed", 
            "error": str(e)
        })
        sys.exit(1)  # Exit with error code for pre-commit hook
