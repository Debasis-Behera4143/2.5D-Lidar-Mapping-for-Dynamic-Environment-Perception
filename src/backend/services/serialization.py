"""
Universal JSON-safety serialization service.

Converts NumPy types, PyTorch tensors, Pydantic models, and nested structures
into pure Python primitives (int, float, bool, str, list, dict) suitable for
FastAPI JSON responses.
"""

from typing import Any
import math
import numpy as np
import torch


def to_json_safe(obj: Any) -> Any:
    """
    Recursively transform arbitrary data structures containing NumPy or PyTorch
    objects into JSON-compliant standard Python types.

    Args:
        obj: Object or container to sanitize.

    Returns:
        Sanitized object containing only native Python primitives.
    """
    # 1. Handle None and basic primitives
    if obj is None or isinstance(obj, (str, bool)):
        return obj

    # 2. PyTorch Tensor
    if isinstance(obj, torch.Tensor):
        return to_json_safe(obj.detach().cpu().numpy())

    # 3. NumPy scalar values
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return 0.0
        return val
    elif isinstance(obj, np.bool_):
        return bool(obj)

    # 4. Standard Python floats (check NaN / Inf)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj

    # 5. Standard Python ints
    if isinstance(obj, int):
        return obj

    # 6. NumPy Arrays
    if isinstance(obj, np.ndarray):
        return to_json_safe(obj.tolist())

    # 7. Pydantic V2 models
    if hasattr(obj, "model_dump"):
        return to_json_safe(obj.model_dump())

    # 8. Dictionaries
    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}

    # 9. Lists, tuples, and sets
    if isinstance(obj, (list, tuple, set)):
        return [to_json_safe(item) for item in obj]

    # 10. Generic objects with __dict__
    if hasattr(obj, "__dict__"):
        return to_json_safe(obj.__dict__)

    # Fallback to string representation
    return str(obj)
