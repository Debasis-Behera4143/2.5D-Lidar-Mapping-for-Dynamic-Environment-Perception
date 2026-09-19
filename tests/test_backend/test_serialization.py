"""
Unit tests for universal JSON serialization service.

Verifies conversion of NumPy scalar types, multi-dimensional arrays, PyTorch tensors,
and nested structures into JSON-safe native Python primitives.
"""

import json
import math
import numpy as np
import pytest
import torch

from src.backend.services.serialization import to_json_safe


class TestSerialization:
    """Test suite for universal to_json_safe converter."""

    def test_numpy_scalar_conversions(self):
        scalars = {
            "int32": np.int32(42),
            "int64": np.int64(100000),
            "float32": np.float32(3.1415),
            "float64": np.float64(2.71828),
            "bool_true": np.bool_(True),
            "bool_false": np.bool_(False),
        }

        sanitized = to_json_safe(scalars)

        assert isinstance(sanitized["int32"], int)
        assert sanitized["int32"] == 42
        assert isinstance(sanitized["int64"], int)
        assert sanitized["int64"] == 100000
        assert isinstance(sanitized["float32"], float)
        assert pytest.approx(sanitized["float32"], abs=1e-4) == 3.1415
        assert isinstance(sanitized["float64"], float)
        assert pytest.approx(sanitized["float64"], abs=1e-5) == 2.71828
        assert isinstance(sanitized["bool_true"], bool)
        assert sanitized["bool_true"] is True
        assert isinstance(sanitized["bool_false"], bool)
        assert sanitized["bool_false"] is False

    def test_numpy_array_conversions(self):
        arr_1d = np.array([1, 2, 3], dtype=np.int64)
        arr_2d = np.array([[1.5, 2.5], [3.5, 4.5]], dtype=np.float32)

        safe_1d = to_json_safe(arr_1d)
        safe_2d = to_json_safe(arr_2d)

        assert isinstance(safe_1d, list)
        assert safe_1d == [1, 2, 3]
        assert all(isinstance(x, int) for x in safe_1d)

        assert isinstance(safe_2d, list)
        assert len(safe_2d) == 2
        assert safe_2d[0] == [1.5, 2.5]
        assert all(isinstance(val, float) for row in safe_2d for val in row)

    def test_torch_tensor_conversions(self):
        tensor_1d = torch.tensor([10, 20, 30], dtype=torch.int64)
        tensor_2d = torch.tensor([[0.1, 0.2], [0.3, 0.4]], dtype=torch.float32)

        safe_t1 = to_json_safe(tensor_1d)
        safe_t2 = to_json_safe(tensor_2d)

        assert isinstance(safe_t1, list)
        assert safe_t1 == [10, 20, 30]
        assert all(isinstance(x, int) for x in safe_t1)

        assert isinstance(safe_t2, list)
        assert len(safe_t2) == 2
        assert pytest.approx(safe_t2[0][0], abs=1e-4) == 0.1

    def test_nested_complex_structures(self):
        payload = {
            "metadata": {"frame_id": "000001", "active": np.bool_(True)},
            "points": np.array([[0.0, 1.0, 2.0]], dtype=np.float32),
            "labels": torch.tensor([5], dtype=torch.int64),
            "scores": [np.float32(0.98), np.float64(0.85)],
            "counts": {"0": np.int64(10), "5": np.int64(2)},
        }

        safe_payload = to_json_safe(payload)

        # Must cleanly dump to standard JSON string without TypeError
        json_str = json.dumps(safe_payload)
        deserialized = json.loads(json_str)

        assert deserialized["metadata"]["active"] is True
        assert deserialized["labels"] == [5]
        assert deserialized["counts"]["5"] == 2

    def test_nan_and_inf_handling(self):
        nan_float = float("nan")
        inf_float = float("inf")
        safe_nan = to_json_safe(nan_float)
        safe_inf = to_json_safe(inf_float)

        assert safe_nan == 0.0
        assert safe_inf == 0.0
        # Check standard json.dumps works
        assert json.dumps({"nan": safe_nan, "inf": safe_inf}) == '{"nan": 0.0, "inf": 0.0}'
