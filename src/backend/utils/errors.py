"""
Domain-specific exceptions for the backend service.
"""


class BackendError(Exception):
    """Base exception for all backend application errors."""
    pass


class CheckpointNotFoundError(BackendError):
    """Raised when the specified model checkpoint file does not exist."""
    pass


class SampleNotFoundError(BackendError):
    """Raised when a requested LiDAR sample frame cannot be found."""
    pass


class SecurityError(BackendError):
    """Raised when a path traversal attempt or unauthorized directory access is detected."""
    pass


class InferenceError(BackendError):
    """Raised when model forward pass or preprocessing fails."""
    pass


class InvalidInputError(BackendError):
    """Raised when input point cloud or parameters violate contract bounds."""
    pass
