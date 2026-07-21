"""Failures raised by the analytics framework."""


class AnalyticsError(Exception):
    """Base class for analytics framework failures."""


class AnalyticsValidationError(AnalyticsError):
    """The supplied analytics dataset is invalid."""
