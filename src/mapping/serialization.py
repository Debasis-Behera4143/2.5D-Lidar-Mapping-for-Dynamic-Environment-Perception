"""
JSON serialization utilities for mapping data structures.

Ensures that all output dictionaries, cell collections, and statistics contain only
standard Python primitives (int, float, str, bool, list, dict) without raw NumPy
or PyTorch types.
"""

import json
from typing import Any
import numpy as np


def to_json_serializable(obj: Any) -> Any:
    """
    Recursively convert NumPy numbers, arrays, and tuples into standard Python primitives.

    Args:
        obj: Arbitrary data structure (dict, list, tuple, numpy type, etc.)

    Returns:
        JSON-compliant object containing only native Python types.
    """
    if isinstance(obj, dict):
        return {str(k): to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return [to_json_serializable(x) for x in obj.tolist()]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, float):
        # Handle NaN or Inf gracefully if needed
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, (int, str, bool)) or obj is None:
        return obj
    elif hasattr(obj, "__dict__"):
        return to_json_serializable(obj.__dict__)
    else:
        # Fallback to string representation
        return str(obj)


def to_json_string(obj: Any, indent: int = 2) -> str:
    """Serialize any mapping output object directly to a JSON formatted string."""
    serializable = to_json_serializable(obj)
    return json.dumps(serializable, indent=indent)
