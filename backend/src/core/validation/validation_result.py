"""
Validation Result Classes
Common validation result structures used across all validators
"""

from dataclasses import dataclass
from typing import List, Any, Optional, Dict
from enum import Enum


class ValidationSeverity(str, Enum):
    """Validation message severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Represents a validation error that prevents successful registration"""
    field: str
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationWarning:
    """Represents a validation warning that doesn't prevent registration"""
    field: str
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Complete validation result with errors, warnings, and success status"""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]

    def __post_init__(self):
        """Automatically set valid=False if there are any errors"""
        if self.errors:
            self.valid = False

    @classmethod
    def success(
        cls, warnings: Optional[List[ValidationWarning]] = None
    ) -> 'ValidationResult':
        """Create a successful validation result"""
        return cls(
            valid=True,
            errors=[],
            warnings=warnings or []
        )

    @classmethod
    def failure(
        cls,
        errors: List[ValidationError],
        warnings: Optional[List[ValidationWarning]] = None
    ) -> 'ValidationResult':
        """Create a failed validation result"""
        return cls(
            valid=False,
            errors=errors,
            warnings=warnings or []
        )

    def add_error(
        self,
        field: str,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Add a validation error"""
        self.errors.append(ValidationError(field, message, code, details))
        self.valid = False

    def add_warning(
        self,
        field: str,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Add a validation warning"""
        self.warnings.append(ValidationWarning(field, message, code, details))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "valid": self.valid,
            "errors": [
                {
                    "field": error.field,
                    "message": error.message,
                    "code": error.code,
                    "details": error.details
                }
                for error in self.errors
            ],
            "warnings": [
                {
                    "field": warning.field,
                    "message": warning.message,
                    "code": warning.code,
                    "details": warning.details
                }
                for warning in self.warnings
            ]
        }
