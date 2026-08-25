"""Contract-First Schema-Driven Validation Package for TranslateGate.

Provides TranslationContract, ContractValidator, and ContractValidationResult.
"""

from translategate.contract.spec import (
    ContractValidationResult,
    ContractViolation,
    TranslationContract,
    ValidationSeverity,
)
from translategate.contract.validator import ContractValidator

__all__ = [
    "ContractValidationResult",
    "ContractValidator",
    "ContractViolation",
    "TranslationContract",
    "ValidationSeverity",
]
