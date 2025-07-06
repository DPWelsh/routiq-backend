"""
Global Utility Functions
Common helper functions used across the application
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
import json
import re
from fastapi.encoders import jsonable_encoder

from src.constants import DateFormats, RESPONSE_TEMPLATES


def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())


def generate_random_string(length: int = 32) -> str:
    """Generate a random string of specified length"""
    return secrets.token_urlsafe(length)


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash a string using the specified algorithm"""
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = DateFormats.ISO_DATETIME) -> str:
    """Format datetime to string"""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = DateFormats.ISO_DATETIME) -> datetime:
    """Parse datetime string to datetime object"""
    return datetime.strptime(dt_str, format_str).replace(tzinfo=timezone.utc)


def datetime_to_gmt_str(dt: datetime) -> str:
    """Convert datetime to GMT string format"""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's between 10-15 digits
    return 10 <= len(digits_only) <= 15


def normalize_phone(phone: str) -> str:
    """Normalize phone number to digits only"""
    return re.sub(r'\D', '', phone)


def sanitize_string(text: str, max_length: int = 255) -> str:
    """Sanitize string input"""
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: Any = None) -> str:
    """Safely serialize object to JSON string"""
    try:
        return json.dumps(jsonable_encoder(obj), default=str)
    except (TypeError, ValueError):
        return json.dumps(default) if default is not None else "{}"


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Flatten nested dictionary"""
    def _flatten(obj, prefix=""):
        items = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}{separator}{key}" if prefix else key
                items.extend(_flatten(value, new_key))
        else:
            items.append((prefix, obj))
        return items
    
    return dict(_flatten(data))


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dictionary"""
    return {k: v for k, v in data.items() if v is not None}


def convert_decimal_to_float(data: Any) -> Any:
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, dict):
        return {k: convert_decimal_to_float(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimal_to_float(item) for item in data]
    return data


def create_success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    status_code: int = 200
) -> Dict[str, Any]:
    """Create standardized success response"""
    response = RESPONSE_TEMPLATES["success"].copy()
    response.update({
        "data": data,
        "message": message,
        "timestamp": utc_now().isoformat()
    })
    return response


def create_error_response(
    error: str,
    message: str = "An error occurred",
    status_code: int = 500
) -> Dict[str, Any]:
    """Create standardized error response"""
    response = RESPONSE_TEMPLATES["error"].copy()
    response.update({
        "error": error,
        "message": message,
        "timestamp": utc_now().isoformat()
    })
    return response


def create_validation_error_response(
    errors: List[str],
    message: str = "Validation failed"
) -> Dict[str, Any]:
    """Create standardized validation error response"""
    response = RESPONSE_TEMPLATES["validation_error"].copy()
    response.update({
        "errors": errors,
        "message": message,
        "timestamp": utc_now().isoformat()
    })
    return response


def calculate_percentage(part: int, total: int) -> float:
    """Calculate percentage with safe division"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def mask_sensitive_data(text: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first/last few characters"""
    if len(text) <= visible_chars * 2:
        return "*" * len(text)
    
    return text[:visible_chars] + "*" * (len(text) - visible_chars * 2) + text[-visible_chars:]


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ""


def bytes_to_human_readable(bytes_count: int) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB" 