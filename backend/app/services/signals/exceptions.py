"""Failures raised by the signal framework."""


class SignalError(Exception):
    """Base class for signal framework failures."""


class DuplicateSignalRuleError(SignalError):
    """More than one registered rule claims the same stable identity."""


class InvalidSignalRuleOutputError(SignalError):
    """A rule returned output that violates its declared contract or provenance."""
