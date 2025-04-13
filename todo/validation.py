"""
Input validation module for the Todo application.
Provides functions to validate and sanitize inputs before they are processed.
"""
import re
import uuid

# Constants
MAX_TITLE_LENGTH = 10000  # Maximum allowed length for task titles
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
)


class ValidationError(Exception):
    """Exception raised for validation errors in inputs."""
    pass


def validate_title(title):
    """
    Validate a task title.
    
    Args:
        title (str): The title to validate
        
    Returns:
        str: The sanitized title
        
    Raises:
        ValidationError: If title is invalid or cannot be sanitized
        TypeError: If title is not a string
    """
    # Type checking
    if not isinstance(title, str):
        raise TypeError(f"Title must be a string, got {type(title).__name__}")
    
    # Check for null bytes which can cause security issues
    if '\0' in title:
        sanitized = title.replace('\0', '')
        if not sanitized:  # If replacing null bytes results in empty string
            raise ValidationError("Title cannot consist only of null bytes")
        return sanitized
    
    # Length validation
    if len(title) > MAX_TITLE_LENGTH:
        sanitized = title[:MAX_TITLE_LENGTH]
        return sanitized
    
    # Return the original or sanitized title
    return title


def validate_task_id(task_id):
    """
    Validate a task ID.
    
    Args:
        task_id (str): The task ID to validate
        
    Returns:
        str: The validated task ID
        
    Raises:
        ValidationError: If task_id is not a valid UUID format
        TypeError: If task_id is not a string
    """
    # Type checking
    if not isinstance(task_id, str):
        raise TypeError(f"Task ID must be a string, got {type(task_id).__name__}")
    
    # Empty check
    if not task_id:
        raise ValidationError("Task ID cannot be empty")
    
    # Format validation using UUID pattern
    if not UUID_PATTERN.match(task_id):
        raise ValidationError(f"Invalid task ID format: {task_id}")
    
    return task_id


def validate_boolean(value):
    """
    Validate and convert a value to boolean
    
    Args:
        value: Value to convert to boolean
        
    Returns:
        bool: Converted boolean value
        
    Raises:
        TypeError: If value cannot be converted to boolean
    """
    if value is None:
        return False
    
    if isinstance(value, bool):
        return value
    
    # Use Union type syntax (X | Y) instead of tuple for isinstance
    if isinstance(value, str | bytes | bytearray):
        lowercase_value = str(value).lower().strip()
        if lowercase_value in ("true", "1", "yes", "y", "t"):
            return True
        if lowercase_value in ("false", "0", "no", "n", "f", ""):
            return False
        raise TypeError(f"Cannot convert string '{value}' to boolean")
    
    if isinstance(value, int | float):
        return bool(value)
    
    raise TypeError(f"Cannot convert {type(value).__name__} to boolean")


def generate_task_id():
    """
    Generate a valid task ID.
    
    Returns:
        str: A new UUID4 string
    """
    return str(uuid.uuid4())
