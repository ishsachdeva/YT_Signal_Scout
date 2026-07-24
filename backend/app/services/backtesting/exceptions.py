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


class GroundTruthLabelImportError(Exception):
    """Base failure for governed ground-truth label import."""


class GroundTruthLabelReadError(GroundTruthLabelImportError):
    """Raised when a ground-truth label file cannot be read."""


class GroundTruthLabelSyntaxError(GroundTruthLabelImportError):
    """Raised when ground-truth label input is not valid JSON."""


class UnsupportedGroundTruthLabelSchemaError(GroundTruthLabelImportError):
    """Raised when a label document declares an unsupported schema."""


class GroundTruthLabelValidationError(GroundTruthLabelImportError):
    """Raised when typed label input violates structural validation."""

    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("ground-truth label validation failed: " + "; ".join(issues))


class GroundTruthLabelDuplicateError(GroundTruthLabelValidationError):
    """Raised when label-set identities are duplicated."""


class GroundTruthLabelDigestMismatchError(GroundTruthLabelValidationError):
    """Raised when canonical labels do not match their declared digest."""


class EvidencePackImportError(Exception):
    """Base failure for governed evidence-pack import."""


class EvidencePackReadError(EvidencePackImportError):
    """Raised when an evidence-pack file cannot be read."""


class EvidencePackSyntaxError(EvidencePackImportError):
    """Raised when evidence-pack input is not valid JSON."""


class UnsupportedEvidencePackSchemaError(EvidencePackImportError):
    """Raised when an evidence-pack document declares an unsupported schema."""


class EvidencePackValidationError(EvidencePackImportError):
    """Raised when typed evidence-pack input is structurally invalid."""

    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("evidence-pack validation failed: " + "; ".join(issues))


class EvidencePackDigestMismatchError(EvidencePackValidationError):
    """Raised when evidence definition or pack digest validation fails."""


class RubricImportError(Exception):
    """Base failure for governed labelling-rubric import."""


class RubricReadError(RubricImportError):
    """Raised when a rubric file cannot be read."""


class RubricSyntaxError(RubricImportError):
    """Raised when rubric input is not valid JSON."""


class UnsupportedRubricSchemaError(RubricImportError):
    """Raised when a rubric document declares an unsupported schema."""


class RubricValidationError(RubricImportError):
    """Raised when typed rubric input is structurally invalid."""

    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("labelling-rubric validation failed: " + "; ".join(issues))


class RubricDigestMismatchError(RubricValidationError):
    """Raised when canonical rubric content does not match its digest."""


class GroundTruthLabelBindingError(ValueError):
    """Raised when a label does not bind its supplied evidence pack and rubric."""


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


class StudyExecutionError(Exception):
    """Base failure for governed, non-analytical study execution."""


class StudyExecutionValidationError(StudyExecutionError):
    """Raised when governed execution inputs do not bind exactly."""

    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("study execution validation failed: " + "; ".join(issues))


class StudyExecutionDigestMismatchError(StudyExecutionValidationError):
    """Raised when canonical execution content differs from its digest."""


class EvaluationError(Exception):
    """Base failure for deterministic observation-level evaluation."""


class EvaluationValidationError(EvaluationError):
    """Raised when labelled-evaluation inputs do not bind exactly."""

    def __init__(self, issues: tuple[str, ...]) -> None:
        self.issues = issues
        super().__init__("labelled evaluation validation failed: " + "; ".join(issues))


class EvaluationDigestMismatchError(EvaluationValidationError):
    """Raised when canonical evaluation content differs from its digest."""
