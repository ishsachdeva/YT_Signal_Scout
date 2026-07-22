"""Failures for structurally invalid offline backtest inputs."""


class BacktestValidationError(ValueError):
    """Raised when a backtest dataset or configuration is structurally invalid."""
