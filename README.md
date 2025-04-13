# Vibe Todo

A high-performance, production-ready Todo application built with Python 3.11+ and SQLite, featuring extensive testing including evolutionary techniques to ensure robustness and security.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- Add, toggle, delete, and list tasks with robust validation
- High performance (10ms SLA for all operations)
- Optimized SQLite database with transaction support
- Comprehensive input validation and sanitization
- Protection against SQL injection and other security issues
- Structured JSON logging for observability

## Requirements

- Python 3.11 or higher
- SQLite3

## Quick Start (with Docker)

The easiest way to run the application is with Docker:

```bash
# Clone the repository
git clone https://github.com/copyleftdev/vibe-todo.git
cd vibe-todo

# Run the application with Docker
docker-compose run app
```

## Manual Installation

```bash
# Clone the repository
git clone https://github.com/copyleftdev/vibe-todo.git
cd vibe-todo

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m todo
```

## API Usage

```python
from todo.models import init_db
from todo.controller import add_task, toggle_done, delete_task, list_tasks

# Initialize database connection
conn = init_db()

# Add a new task
task = add_task(conn, "Complete the project")
print(f"Added task: {task}")

# Toggle a task's status
updated_task = toggle_done(conn, task['id'])
print(f"Toggled task: {updated_task}")

# List all tasks
all_tasks = list_tasks(conn)
print(f"All tasks: {all_tasks}")

# List only completed tasks
done_tasks = list_tasks(conn, done=True)
print(f"Completed tasks: {done_tasks}")

# Delete a task
delete_task(conn, task['id'])
print("Task deleted")
```

## Development

### Running Tests

The project includes comprehensive test suites:

```bash
# Run all tests with Docker (excluding evolutionary tests)
docker-compose run test-all

# Run all tests including evolutionary tests
docker-compose run test-all-evolutionary

# Run specific test suites
docker-compose run test-unit
docker-compose run test-regression
docker-compose run test-benchmark
docker-compose run test-evolutionary
```

For local development:

```bash
# Run all tests
python run_all_tests.py

# Run all tests including evolutionary tests
python run_all_tests.py --evolutionary

# Run tests in quick mode
python run_all_tests.py --quick
```

### Linting

```bash
# Run linting with Docker
docker-compose run lint

# Run linting locally
ruff check .
black --check .
mypy todo tests
```

### Pre-commit Hooks

The repository includes a pre-commit hook that runs tests before allowing commits:

```bash
# Set up the pre-commit hook
python setup_hooks.py
```

## Architecture

The application follows a modular architecture:

- `todo/models.py` - Database initialization and schema
- `todo/controller.py` - Core business logic and database operations
- `todo/validation.py` - Input validation and sanitization
- `tests/` - Comprehensive test suites

## Testing Philosophy

The project embraces thorough testing:

1. **Unit Tests** - Basic functionality validation
2. **Hypothesis Tests** - Property-based tests with randomized inputs
3. **Regression Tests** - Tests for known edge cases
4. **Benchmark Tests** - Performance tests to ensure SLA compliance
5. **Evolutionary Tests** - Uses DEAP to evolve inputs that might break the system

## SLA Compliance

All operations must meet a Service-Level Agreement (SLA) of **10 milliseconds maximum latency per task operation**. The benchmark tests verify this requirement continuously.

## Security

The application employs several security measures:

- All user inputs are validated and sanitized
- Protection against SQL injection
- Proper handling of special characters and large inputs
- Transaction-based operations with rollback capability

## Version History

- **1.0.0** (2025-04-13) - Initial release with core functionality, Docker support, and comprehensive testing

## License

This project is licensed under the MIT License - see the LICENSE file for details.
