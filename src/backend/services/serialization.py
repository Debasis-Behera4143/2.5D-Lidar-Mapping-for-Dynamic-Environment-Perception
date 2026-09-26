"""
Universal JSON-safety serialization service.

Converts NumPy types, PyTorch tensors, Pydantic models, and nested structures
into pure Python primitives (int, float, bool, str, list, dict) suitable for
FastAPI JSON responses.

torch is checked lazily via sys.modules to avoid forcing a top-level import.
"""

from typing import Any
import math
import sys
import numpy as np


def _is_torch_tensor(obj):
    """Check if obj is a torch.Tensor without requiring torch at import time."""
    torch_mod = sys.modules.get("torch")
    if torch_mod is not None:
        return isinstance(obj, torch_mod.Tensor)
    return False


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

    # 2. PyTorch Tensor (lazy check)
    if _is_torch_tensor(obj):
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
