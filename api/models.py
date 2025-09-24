"""
Pydantic models for API request/response validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class LogLevel(str, Enum):
    """Logging level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    server: str = Field(..., description="SQL Server hostname or IP")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    driver: str = Field(default="ODBC Driver 17 for SQL Server", description="ODBC driver name")


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str = Field(..., description="OpenAI API key")
    model: str = Field(default="gpt-4", description="OpenAI model to use")


class GenerationConfig(BaseModel):
    """Q&A generation configuration."""
    sample_size: int = Field(default=10, ge=1, le=100, description="Number of sample rows per table")
    min_questions: int = Field(default=25, ge=5, le=100, description="Total number of questions to generate")
    target_join_percentage: int = Field(default=40, ge=0, le=100, description="Target percentage of join questions")
    max_tables: int = Field(default=12, ge=2, le=50, description="Maximum number of tables to include in generation (to prevent token overflow)")
    output_file: Optional[str] = Field(default=None, description="Output file name (optional)")


class DiscoveryRequest(BaseModel):
    """Request model for database discovery."""
    database_config: DatabaseConfig
    exclude_tables: List[str] = Field(default_factory=list, description="Tables to exclude from discovery")
    min_tables: int = Field(default=2, ge=1, description="Minimum number of tables required")
    max_tables: int = Field(default=10, ge=2, le=20, description="Maximum number of tables to analyze")


class TableInfo(BaseModel):
    """Table information model."""
    name: str
    column_count: int
    columns: List[Dict[str, Any]]


class RelationshipInfo(BaseModel):
    """Foreign key relationship information."""
    fk_name: str
    parent_table: str
    parent_column: str
    referenced_table: str
    referenced_column: str


class DiscoveryResponse(BaseModel):
    """Response model for database discovery."""
    success: bool
    message: str
    tables: List[TableInfo] = Field(default_factory=list)
    relationships: List[RelationshipInfo] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    suggested_tables: List[str] = Field(default_factory=list)
    join_potential: float = Field(default=0.0, description="Percentage indicating join potential")


class GenerationRequest(BaseModel):
    """Request model for Q&A generation."""
    database_config: DatabaseConfig
    openai_config: OpenAIConfig
    generation_config: GenerationConfig = Field(default_factory=GenerationConfig)
    tables: Optional[List[str]] = Field(default=None, description="Specific tables to analyze")
    discover_all: bool = Field(default=False, description="Auto-discover all tables")
    exclude_tables: List[str] = Field(default_factory=list, description="Tables to exclude")

    @model_validator(mode='after')
    def validate_table_selection(self):
        """Validate that either tables or discover_all is specified."""
        tables = self.tables
        discover_all = self.discover_all
        
        if not discover_all and not tables:
            raise ValueError('Either tables list or discover_all must be specified')
        if discover_all and tables:
            raise ValueError('Cannot specify both tables and discover_all')
        return self


class QAPair(BaseModel):
    """Question-Answer pair model."""
    question: str
    expected_answer: str


class GenerationResponse(BaseModel):
    """Response model for Q&A generation."""
    success: bool
    message: str
    dataset: List[QAPair] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    token_usage: Optional[Dict[str, Any]] = Field(default=None, description="AI token usage information")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None


class TableSelectionRequest(BaseModel):
    """Request model for table selection after discovery."""
    database_config: DatabaseConfig
    selected_tables: List[str] = Field(..., min_items=2, description="Selected table names")

    @field_validator('selected_tables')
    @classmethod
    def validate_minimum_tables(cls, v):
        """Validate minimum number of tables."""
        if len(v) < 2:
            raise ValueError('At least 2 tables must be selected')
        return v


class AsyncJobRequest(BaseModel):
    """Request model for asynchronous job processing."""
    job_type: str = Field(..., description="Type of job: 'discovery' or 'generation'")
    request_data: Dict[str, Any] = Field(..., description="Job-specific request data")


class AsyncJobResponse(BaseModel):
    """Response model for asynchronous job status."""
    job_id: str
    status: str = Field(..., description="Job status: 'pending', 'running', 'completed', 'failed'")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Job progress percentage")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Job result when completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: str
    updated_at: str


class SimpleGenerationRequest(BaseModel):
    """Simplified request model for Q&A generation using environment config."""
    tables: List[str] = Field(default_factory=list, description="List of table names to analyze (empty for auto-discovery)")
    questions_per_table: int = Field(default=25, ge=5, le=100, description="Total number of Q&A pairs to generate")
    max_tables: int = Field(default=12, ge=2, le=50, description="Maximum number of tables for auto-discovery")
    include_joins: bool = Field(default=True, description="Include join-based questions")
    difficulty_level: str = Field(default="mixed", description="Question difficulty level")
    output_file: Optional[str] = Field(default=None, description="Output file name (optional)")
