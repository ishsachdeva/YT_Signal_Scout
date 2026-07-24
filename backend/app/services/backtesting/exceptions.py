"""Failures for structurally invalid offline backtest inputs."""


class BacktestValidationError(ValueError):
    """Raised when a backtest dataset or configuration is structurally invalid."""


class HistoricalDatasetImportError(Exception):
    """Base failure for governed historical dataset import."""


class HistoricalDatasetReadError(HistoricalDatasetImportError):
    """Raised when a historical dataset file cannot be read."""


class HistoricalDatasetSyntaxError(HistoricalDatasetImportError):
    """Raised when input is not syntactically valid JSON."""


class UnsupportedHistoricalDatasetSchemaError(HistoricalDatasetImportError):
    """Raised when an input declares an unsupported schema version."""


class HistoricalDatasetValidationError(HistoricalDatasetImportError):
    """Raised when typed historical input violates structural validation."""

    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("historical dataset validation failed: " + "; ".join(issues))


class HistoricalDatasetDuplicateError(HistoricalDatasetValidationError):
    """Raised when governed observation identity rules are violated."""


class HistoricalDatasetDigestMismatchError(HistoricalDatasetValidationError):
    """Raised when canonical dataset content does not match its declared digest."""


class BacktestExecutionError(Exception):
    """Base failure for controlled offline backtest execution."""


class InvalidBacktestExecutionRequestError(BacktestExecutionError):
    """Raised when execution does not receive its typed immutable request."""


class BacktestExecutionDatasetMismatchError(BacktestExecutionError):
    """Raised when execution output or configuration targets another dataset."""


class BacktestExecutionConfigurationMismatchError(BacktestExecutionError):
    """Raised when execution output does not match the requested configuration."""


class BacktestExecutionStructuralError(BacktestExecutionError):
    """Raised when the backtester rejects or returns an invalid structure."""
