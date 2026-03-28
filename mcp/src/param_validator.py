"""Parameter validation utilities for MCP tools.

This module provides functions to validate that required parameters are provided
and not empty/invalid before executing tool logic. This prevents tools from
returning success when they should fail due to missing parameters.
"""

from typing import Any, Dict, Optional, List
import functools


def validate_required_params(**param_definitions) -> callable:
    """Decorator to validate required parameters before executing a tool function.
    
    Args:
        **param_definitions: Keyword arguments where key is parameter name and 
                           value is a dict with 'required': bool and optional 'type': type
    
    Example:
        @validate_required_params(
            database_name={'required': True, 'type': str},
            timeout={'required': False, 'type': int}
        )
        async def switch_database(database_name: str, timeout: int = 30):
            ...
    
    Returns:
        Decorator function that performs validation before calling the original function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get function signature to map positional args to param names
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each defined parameter
            for param_name, rules in param_definitions.items():
                if not rules.get('required', False):
                    continue
                    
                # Get the actual value passed
                value = bound_args.arguments.get(param_name)
                
                # Check if parameter is missing, None, or empty string
                if value is None:
                    return {
                        "error": f"Missing required parameter: '{param_name}'",
                        "parameter": param_name,
                        "status": "validation_failed"
                    }
                
                if isinstance(value, str) and value.strip() == "":
                    return {
                        "error": f"Required parameter '{param_name}' cannot be empty",
                        "parameter": param_name,
                        "status": "validation_failed"
                    }
                
                # Check type if specified
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    return {
                        "error": f"Parameter '{param_name}' must be of type {expected_type.__name__}, got {type(value).__name__}",
                        "parameter": param_name,
                        "expected_type": expected_type.__name__,
                        "actual_type": type(value).__name__,
                        "status": "validation_failed"
                    }
            
            # All validations passed, call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_params(params: Dict[str, Any], required: List[str]) -> Optional[Dict[str, str]]:
    """Validate that required parameters are present and not empty.
    
    Args:
        params: Dictionary of parameters to validate
        required: List of required parameter names
    
    Returns:
        None if validation passes, otherwise a dict with error information
    
    Example:
        error = validate_params(
            {"database_name": "", "catalog": "main"},
            ["database_name", "catalog"]
        )
        if error:
            return error
    """
    for param_name in required:
        # Check if parameter is missing
        if param_name not in params:
            return {
                "error": f"Missing required parameter: '{param_name}'",
                "parameter": param_name,
                "status": "validation_failed"
            }
        
        value = params[param_name]
        
        # Check if parameter is None
        if value is None:
            return {
                "error": f"Required parameter '{param_name}' cannot be None",
                "parameter": param_name,
                "status": "validation_failed"
            }
        
        # Check if parameter is empty string
        if isinstance(value, str) and value.strip() == "":
            return {
                "error": f"Required parameter '{param_name}' cannot be empty",
                "parameter": param_name,
                "status": "validation_failed"
            }
    
    return None


def ensure_non_empty(value: Any, param_name: str) -> Optional[Dict[str, str]]:
    """Quick validation helper for a single parameter.
    
    Args:
        value: The value to validate
        param_name: Name of the parameter (for error message)
    
    Returns:
        None if valid, otherwise error dict
    
    Example:
        if error := ensure_non_empty(database_name, "database_name"):
            return error
    """
    if value is None:
        return {
            "error": f"Missing required parameter: '{param_name}'",
            "parameter": param_name,
            "status": "validation_failed"
        }
    
    if isinstance(value, str) and value.strip() == "":
        return {
            "error": f"Required parameter '{param_name}' cannot be empty",
            "parameter": param_name,
            "status": "validation_failed"
        }
    
    return None
