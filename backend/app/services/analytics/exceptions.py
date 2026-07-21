"""Failures raised by the analytics framework."""


class AnalyticsError(Exception):
    """Base class for analytics framework failures."""


class AnalyticsValidationError(AnalyticsError):
    """The supplied analytics dataset is invalid."""


class DuplicateCalculatorError(AnalyticsError):
    """More than one registered calculator produces the same metric."""


class AnalyticsAssemblyError(AnalyticsError):
    """Metric results cannot form a complete analytics aggregate."""
