"""
Custom exceptions for GenAI SQL Test Data Generator.
"""


class QNAGeneratorError(Exception):
    """Base exception for QNA Generator application."""
    pass


class DatabaseConnectionError(QNAGeneratorError):
    """Raised when database connection fails."""
    pass


class SchemaDiscoveryError(QNAGeneratorError):
    """Raised when schema discovery fails."""
    pass


class LLMGenerationError(QNAGeneratorError):
    """Raised when LLM generation fails."""
    pass


class ValidationError(QNAGeneratorError):
    """Raised when data validation fails."""
    pass
