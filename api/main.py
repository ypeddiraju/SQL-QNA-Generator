"""
FastAPI main application for GenAI SQL Test Data Generator.

This module provides REST API endpoints for:
- Database discovery and schema analysis
- Q&A dataset generation
- Health checks and status monitoring
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from api.models import (
    DiscoveryRequest, DiscoveryResponse, TableInfo, RelationshipInfo,
    GenerationRequest, GenerationResponse, QAPair,
    HealthResponse, ErrorResponse, AsyncJobResponse,
    DatabaseConfig, OpenAIConfig, GenerationConfig, SimpleGenerationRequest, SimpleDiscoveryRequest
)
from src.database_connector import DatabaseConnector
from src.llm_generator import LLMGenerator
from src.config import Config
from src.exceptions import QNAGeneratorError, DatabaseConnectionError, LLMGenerationError
from src.demo_data import DEMO_TABLES, DEMO_RELATIONSHIPS, DEMO_SAMPLE_DATA


# Initialize FastAPI app
app = FastAPI(
    title="GenAI SQL Test Data Generator API",
    description="REST API for generating Q&A test datasets from SQL Server databases using LLM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Difficulty level to join percentage mapping
def get_target_join_percentage(difficulty_level: str, default_percentage: int = 40) -> int:
    """
    Map difficulty levels to target join percentages.
    
    Args:
        difficulty_level: The difficulty level (easy, medium, hard, mixed)
        default_percentage: Default percentage if difficulty not recognized
        
    Returns:
        Target join percentage for the difficulty level
    """
    difficulty_mapping = {
        "easy": 20,      # 20% joins - mostly simple single-table queries
        "medium": 40,    # 40% joins - balanced mix (default)
        "hard": 70,      # 70% joins - mostly complex multi-table queries
        "mixed": 40      # 40% joins - balanced variety
    }
    
    return difficulty_mapping.get(difficulty_level.lower(), default_percentage)

# Load environment variables from .env file
load_dotenv()

# Global configuration instance (loaded from .env)
try:
    global_config = Config()
    logging.info("Configuration loaded from environment variables")
    logging.info(f"DB Server: {global_config.db_server}")
    logging.info(f"OpenAI Model: {global_config.openai_model}")
except Exception as e:
    logging.error(f"Failed to load configuration: {e}")
    # Create an empty config for API-only mode
    global_config = None

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory job storage (use Redis/database in production)
job_storage: Dict[str, Dict[str, Any]] = {}


def create_config_from_request(db_config: DatabaseConfig, openai_config: Optional[OpenAIConfig] = None) -> Config:
    """Create application config from API request."""
    # Temporarily set environment variables
    os.environ['DB_SERVER'] = db_config.server
    os.environ['DB_DATABASE'] = db_config.database
    os.environ['DB_USERNAME'] = db_config.username
    os.environ['DB_PASSWORD'] = db_config.password
    os.environ['DB_TYPE'] = db_config.db_type.value
    
    if db_config.driver:
        os.environ['DB_DRIVER'] = db_config.driver
    if db_config.port:
        os.environ['DB_PORT'] = str(db_config.port)
    
    if openai_config:
        os.environ['OPENAI_API_KEY'] = openai_config.api_key
        os.environ['OPENAI_MODEL'] = openai_config.model
    
    try:
        return Config()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}"
        )


def handle_exceptions(func):
    """Decorator to handle common exceptions."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DatabaseConnectionError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connection failed: {str(e)}"
            )
        except LLMGenerationError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM generation failed: {str(e)}"
            )
        except QNAGeneratorError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return wrapper


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main web UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api", response_model=Dict[str, str])
async def api_root():
    """API root endpoint with basic information."""
    return {
        "service": "GenAI SQL Test Data Generator API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "ui": "/"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/api/test-connection")
async def test_database_connection_with_config(request: dict):
    """Test database connection with provided configuration."""
    try:
        # Extract database config from request
        db_config_data = request.get('database_config')
        if not db_config_data:
            raise HTTPException(status_code=400, detail="Missing database_config in request")
        
        # Create DatabaseConfig object
        db_config = DatabaseConfig(**db_config_data)
        
        # Create configuration from request
        config = create_config_from_request(db_config)
        
        logger.info(f"Testing {config.db_type} database connection to {config.db_server}")
        
        # Initialize database connector
        db_connector = DatabaseConnector(config)
        
        # Test connection
        if db_connector.test_connection():
            return {
                "success": True,
                "message": f"{config.db_type.upper()} connection successful",
                "config": {
                    "db_type": config.db_type,
                    "server": config.db_server,
                    "database": config.db_database,
                    "port": config.db_port
                }
            }
        else:
            raise DatabaseConnectionError("Connection failed")
            
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
    except DatabaseConnectionError as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=503, detail={
            "success": False,
            "message": f"Database connection failed: {str(e)}",
            "suggestions": [
                "Check if the database server is running and accessible",
                "Verify network connectivity and firewall settings", 
                "Ensure the credentials are correct",
                "Check if the database name exists",
                "For SQL Server: Verify server allows remote connections",
                "For MySQL: Check if user has proper permissions"
            ]
        })
    except Exception as e:
        logger.error(f"Unexpected error during connection test: {e}")
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        })

@app.post("/api/test-openai")
async def test_openai_connection(request: dict):
    """Test OpenAI API connection with provided configuration."""
    try:
        # Extract OpenAI config from request
        openai_config_data = request.get('openai_config')
        if not openai_config_data:
            raise HTTPException(status_code=400, detail="Missing openai_config in request")
        
        # Create OpenAIConfig object
        openai_config = OpenAIConfig(**openai_config_data)
        
        logger.info(f"Testing OpenAI connection with model {openai_config.model}")
        
        # Test OpenAI connection with a simple API call
        from openai import OpenAI
        client = OpenAI(api_key=openai_config.api_key)
        
        # Make a minimal test call
        response = client.chat.completions.create(
            model=openai_config.model,
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1,
            temperature=0
        )
        
        return {
            "success": True,
            "message": "OpenAI connection successful",
            "model": openai_config.model,
            "test_response": response.choices[0].message.content if response.choices else "Test completed"
        }
        
    except ValueError as e:
        logger.error(f"OpenAI configuration validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid OpenAI configuration: {str(e)}")
    except Exception as e:
        error_message = str(e)
        logger.error(f"OpenAI connection test failed: {error_message}")
        
        # Provide helpful error messages based on common issues
        suggestions = []
        if "api_key" in error_message.lower():
            suggestions.extend([
                "Check if your OpenAI API key is correct",
                "Ensure the API key starts with 'sk-'",
                "Verify the API key has not expired"
            ])
        elif "model" in error_message.lower():
            suggestions.extend([
                "Check if the selected model is available",
                "Verify you have access to the requested model",
                "Try using 'gpt-3.5-turbo' as a fallback"
            ])
        elif "quota" in error_message.lower() or "billing" in error_message.lower():
            suggestions.extend([
                "Check your OpenAI account billing status",
                "Verify you have sufficient API credits"
            ])
        else:
            suggestions.extend([
                "Check your internet connection",
                "Verify the OpenAI API is accessible from your network"
            ])
        
        raise HTTPException(status_code=503, detail={
            "success": False,
            "message": f"OpenAI connection failed: {error_message}",
            "suggestions": suggestions
        })

@app.post("/api/database/test-connection")
async def test_database_connection():
    """Test database connection using current configuration with extended timeouts."""
    try:
        if global_config is None:
            raise HTTPException(status_code=500, detail="Configuration not available")
        
        logger.info(f"Testing database connection with timeouts: connection={global_config.db_connection_timeout}s, login={global_config.db_login_timeout}s")
        
        # Initialize database connector with global config
        db_connector = DatabaseConnector(global_config)
        
        # Test connection with retry logic
        if db_connector.test_connection():
            return {
                "status": "success", 
                "message": "Database connection successful",
                "config": {
                    "server": global_config.db_server,
                    "database": global_config.db_database,
                    "connection_timeout": global_config.db_connection_timeout,
                    "login_timeout": global_config.db_login_timeout,
                    "retry_count": global_config.db_retry_count
                }
            }
        else:
            raise DatabaseConnectionError("Connection failed")
            
    except DatabaseConnectionError as e:
        logger.error(f"Database connection failed after all retries: {e}")
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "Database connection failed",
                "message": str(e),
                "suggestions": [
                    "Check if the SQL Server is running and accessible",
                    "Verify firewall settings allow connections on port 1433",
                    "Ensure the server allows remote connections",
                    "Check if the credentials are correct",
                    "Try increasing timeout values in .env file"
                ]
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during connection test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/database/discover")
async def discover_database_simple(request: SimpleDiscoveryRequest):
    """Discover database using active connection."""
    try:
        from src.config import Config
        
        # Check if there's an active connection
        if not Config.has_active_connection():
            raise HTTPException(
                status_code=400, 
                detail="No active database connection. Please start a connection first in the Config tab."
            )
        
        # Get the active connector
        db_connector = Config.get_active_connector()
        active_config = Config.get_active_config()
        
        if not db_connector or not active_config:
            raise HTTPException(
                status_code=500, 
                detail="Active connection is invalid. Please restart the connection."
            )
        
        logger.info(f"Using active {active_config.db_type} connection for discovery")
        
        # Discover all tables using active connection
        all_tables = await discover_all_tables_async(db_connector)
        
        # Apply basic filters (exclude common system tables)
        exclude_patterns = ['sys', 'temp', 'log', 'audit', 'trace', 'information_schema']
        
        # Add user-specified exclude tables
        if request.exclude_tables:
            user_excludes = [table.strip() for table in request.exclude_tables.split(',') if table.strip()]
            exclude_patterns.extend(user_excludes)
        
        filtered_tables = [
            table for table in all_tables 
            if not any(pattern.lower() in table.lower() for pattern in exclude_patterns)
        ]
        
        # Use all filtered tables - no limit for complete schema discovery
        limited_tables = filtered_tables
        
        logger.info(f"Discovered {len(limited_tables)} tables")
        
        # Get schemas and relationships - handle inaccessible tables gracefully
        try:
            schemas = db_connector.get_table_schemas(limited_tables)
            if not schemas:
                raise QNAGeneratorError("No accessible tables found")
            
            # Update limited_tables to only include accessible ones
            accessible_tables = list(schemas.keys())
            if len(accessible_tables) < len(limited_tables):
                skipped = [t for t in limited_tables if t not in accessible_tables]
                logger.warning(f"Skipped {len(skipped)} inaccessible tables during discovery: {skipped}")
                limited_tables = accessible_tables
            
            relationships = db_connector.get_table_relationships(limited_tables)
            
        except Exception as e:
            logger.error(f"Failed to analyze table schemas: {e}")
            raise QNAGeneratorError(f"Schema analysis failed: {e}")
        
        # Convert to response format
        tables_info = []
        for table in limited_tables:
            if table in schemas:
                columns = [
                    {"name": col["column_name"], "type": col["data_type"], "nullable": col.get("is_nullable", True)}
                    for col in schemas[table]
                ]
                tables_info.append({
                    "name": table,
                    "columns": columns,
                    "row_count": None  # Could add row count if needed
                })
        
        relationships_info = [
            {
                "parent_table": rel["parent_table"],
                "parent_column": rel["parent_column"],
                "child_table": rel["referenced_table"],
                "child_column": rel["referenced_column"]
            }
            for rel in relationships
        ]
        
        return {
            "tables": tables_info,
            "relationships": relationships_info,
            "total_tables": len(all_tables),
            "filtered_tables": len(filtered_tables),
            "total_columns": sum(len(schema) for schema in schemas.values()),
            "message": f"Successfully discovered {len(tables_info)} tables with {len(relationships_info)} relationships"
        }
        
    except DatabaseConnectionError as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/discover", response_model=DiscoveryResponse)
async def discover_database(request: DiscoveryRequest):
    """
    Discover database tables, schemas, and relationships.
    
    This endpoint analyzes the database structure and provides:
    - List of all available tables
    - Table schemas with column information  
    - Foreign key relationships
    - Recommendations for Q&A generation
    """
    logger.info("Starting database discovery")
    
    # Create configuration
    config = create_config_from_request(request.database_config)
    
    # Initialize database connector
    db_connector = DatabaseConnector(config)
    
    # Test connection
    if not db_connector.test_connection():
        raise DatabaseConnectionError("Failed to connect to database")
    
    # Discover all tables
    all_tables = await discover_all_tables_async(db_connector)
    
    # Apply filters
    filtered_tables = [
        table for table in all_tables 
        if not any(excluded.lower() in table.lower() for excluded in request.exclude_tables)
    ]
    
    # Use all filtered tables if max_tables is not specified or set to a high value
    max_limit = request.max_tables if request.max_tables and request.max_tables > 0 else len(filtered_tables)
    analysis_tables = filtered_tables[:max_limit]
    
    if len(analysis_tables) < request.min_tables:
        return DiscoveryResponse(
            success=False,
            message=f"Found only {len(analysis_tables)} tables, minimum {request.min_tables} required"
        )
    
    # Get schemas and relationships
    schemas = db_connector.get_table_schemas(analysis_tables)
    relationships = db_connector.get_table_relationships(analysis_tables)
    
    # Build response
    table_info = []
    for table_name, columns in schemas.items():
        table_info.append(TableInfo(
            name=table_name,
            column_count=len(columns),
            columns=columns
        ))
    
    relationship_info = [
        RelationshipInfo(**rel) for rel in relationships
    ]
    
    # Calculate join potential
    join_potential = min(100.0, (len(relationships) / len(analysis_tables)) * 100) if analysis_tables else 0.0
    
    # Generate recommendations
    recommendations = generate_recommendations(analysis_tables, relationships, join_potential)
    
    # Suggest optimal table selection
    suggested_tables = suggest_optimal_tables(analysis_tables, relationships, request.max_tables)
    
    logger.info(f"Discovery completed: {len(table_info)} tables, {len(relationship_info)} relationships")
    
    return DiscoveryResponse(
        success=True,
        message=f"Successfully analyzed {len(table_info)} tables",
        tables=table_info,
        relationships=relationship_info,
        recommendations=recommendations,
        suggested_tables=suggested_tables,
        join_potential=join_potential
    )


@app.post("/generate", response_model=GenerationResponse)
async def generate_dataset(request: GenerationRequest):
    """
    Generate Q&A dataset from database tables.
    
    This endpoint creates a comprehensive Q&A dataset by:
    - Analyzing table schemas and relationships
    - Sampling relational data
    - Using LLM to generate diverse questions and accurate answers
    """
    logger.info("Starting Q&A dataset generation")
    
    # Create configuration
    config = create_config_from_request(request.database_config, request.openai_config)
    
    # Override config with generation settings (with safety limits)
    config.sample_size = min(request.generation_config.sample_size, 5)  # Max 5 rows per table
    config.min_questions = min(request.generation_config.min_questions, 100)  # Max 100 questions (increased from 15)
    config.target_join_percentage = request.generation_config.target_join_percentage
    if request.generation_config.output_file:
        config.output_file = request.generation_config.output_file
    
    # Initialize connectors
    db_connector = DatabaseConnector(config)
    llm_generator = LLMGenerator(config)
    
    # Test database connection
    if not db_connector.test_connection():
        raise DatabaseConnectionError("Failed to connect to database")
    
    # Determine target tables
    if request.discover_all:
        all_tables = await discover_all_tables_async(db_connector)
        filtered_tables = [
            table for table in all_tables 
            if not any(excluded.lower() in table.lower() for excluded in request.exclude_tables)
        ]
        
        # Intelligent table selection to stay within token limits
        # You can increase this limit, but be aware of potential token overflow issues with LLM
        max_tables = request.generation_config.max_tables  # Configurable limit, default is 12
        
        if len(filtered_tables) <= max_tables:
            target_tables = filtered_tables
        else:
            # Get relationships first to prioritize connected tables
            all_relationships = db_connector.get_table_relationships(filtered_tables[:20])  # Sample relationships
            
            # Find tables with most relationships (core business entities)
            table_relationship_count = {}
            for rel in all_relationships:
                table_relationship_count[rel['parent_table']] = table_relationship_count.get(rel['parent_table'], 0) + 1
                table_relationship_count[rel['referenced_table']] = table_relationship_count.get(rel['referenced_table'], 0) + 1
            
            # Sort tables by relationship count (descending) and take top tables
            sorted_tables = sorted(filtered_tables, 
                                 key=lambda t: table_relationship_count.get(t, 0), 
                                 reverse=True)
            target_tables = sorted_tables[:max_tables]
            
        logger.info(f"Auto-discovered {len(filtered_tables)} tables, selected {len(target_tables)} most connected tables for generation")
    else:
        target_tables = request.tables
        logger.info(f"Using specified tables: {target_tables}")
    
    if len(target_tables) < 2:
        raise QNAGeneratorError("At least 2 tables are required for meaningful Q&A generation")
    
    # Analyze database - handle cases where some tables are inaccessible
    try:
        schemas = db_connector.get_table_schemas(target_tables)
        if not schemas:
            raise QNAGeneratorError("No accessible tables found among the specified tables")
        
        # Update target_tables to only include accessible tables
        accessible_tables = list(schemas.keys())
        if len(accessible_tables) < len(target_tables):
            skipped = [t for t in target_tables if t not in accessible_tables]
            logger.warning(f"Skipped {len(skipped)} inaccessible tables: {skipped}")
            target_tables = accessible_tables
        
        relationships = db_connector.get_table_relationships(target_tables)
        
        logger.info(f"Analyzed {len(schemas)} accessible tables with {len(relationships)} relationships")
        
    except Exception as e:
        logger.error(f"Failed to analyze database structure: {e}")
        raise QNAGeneratorError(f"Database analysis failed: {e}")
    
    if len(target_tables) < 2:
        raise QNAGeneratorError(f"At least 2 accessible tables are required for Q&A generation. Only {len(target_tables)} tables are accessible.")
    
    # Sample data - use the first accessible table
    primary_table = target_tables[0]
    try:
        sample_data = db_connector.get_relational_sample(
            primary_table, target_tables, config.sample_size
        )
    except Exception as e:
        logger.error(f"Failed to sample data from tables: {e}")
        raise QNAGeneratorError(f"Data sampling failed: {e}")
    
    logger.info("Collected relational sample data")
    
    # Generate Q&A dataset
    qna_dataset, token_usage = llm_generator.generate_qna_dataset(
        schemas=schemas,
        relationships=relationships,
        sample_data=sample_data,
        table_names=target_tables
    )
    
    # Calculate statistics
    join_questions = sum(
        1 for item in qna_dataset 
        if llm_generator.requires_join(item['question'], target_tables)
    )
    join_percentage = (join_questions / len(qna_dataset)) * 100 if qna_dataset else 0
    
    # Build response
    qa_pairs = [QAPair(question=item['question'], expected_answer=item['expected_answer']) 
                for item in qna_dataset]
    
    metadata = {
        'tables_analyzed': target_tables,
        'table_count': len(target_tables),
        'relationship_count': len(relationships),
        'sample_size': config.sample_size,
        'generation_timestamp': datetime.utcnow().isoformat()
    }
    
    statistics = {
        'total_questions': len(qna_dataset),
        'join_questions': join_questions,
        'join_percentage': round(join_percentage, 1),
        'single_table_questions': len(qna_dataset) - join_questions,
        'target_join_percentage': config.target_join_percentage,
        'meets_target': join_percentage >= config.target_join_percentage
    }
    
    logger.info(f"Generated {len(qna_dataset)} Q&A pairs ({join_percentage:.1f}% joins)")
    
    return GenerationResponse(
        success=True,
        message=f"Successfully generated {len(qna_dataset)} Q&A pairs",
        dataset=qa_pairs,
        metadata=metadata,
        statistics=statistics,
        token_usage=token_usage
    )


@app.post("/api/generate/dataset", response_model=GenerationResponse)
async def api_generate_dataset(request: SimpleGenerationRequest):
    """API endpoint for Q&A dataset generation using active connection."""
    try:
        logger.info(f"Received generation request: {request}")
        
        # Check if there's an active connection
        if not Config.has_active_connection():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active database connection. Please start a connection first in the Config tab."
            )
        
        # Get the active connection components
        active_config = Config.get_active_config()
        db_connector = Config.get_active_connector()
        
        if not active_config or not db_connector:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Active connection is invalid. Please restart the connection."
            )
        
        # Set difficulty level from request
        active_config.difficulty_level = request.difficulty_level
        
        # Check if OpenAI is configured in the active config
        if not active_config.is_openai_configured():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI configuration not available. Please configure OpenAI API key first."
            )
        
        # Determine if we should auto-discover tables
        discover_all = len(request.tables) == 0
        tables = request.tables if not discover_all else None
        
        logger.info(f"discover_all={discover_all}, tables={tables}")
        
        # Map difficulty level to target join percentage
        target_join_percentage = get_target_join_percentage(
            request.difficulty_level, 
            default_percentage=active_config.target_join_percentage
        )
        
        logger.info(f"Using difficulty level '{request.difficulty_level}' with {target_join_percentage}% target join percentage")
        
        # Direct generation using active connection components
        logger.info("Starting direct generation with active connection")
        
        # Determine target tables using active connection
        if discover_all:
            # Auto-discover tables using the active connector
            all_tables = await discover_all_tables_async(db_connector)
            
            # Apply basic filters with enhanced filtering
            exclude_patterns = ['sys', 'temp', 'log', 'audit', 'trace', 'information_schema', 'mysql', 'performance_schema']
            
            filtered_tables = [
                table for table in all_tables 
                if not any(pattern.lower() in table.lower() for pattern in exclude_patterns)
            ]
            
            # Limit tables to prevent token overflow and select most connected ones
            max_tables = min(request.max_tables, len(filtered_tables))
            
            if len(filtered_tables) <= max_tables:
                target_tables = filtered_tables
            else:
                # Get a sample of relationships to prioritize connected tables
                sample_relationships = db_connector.get_table_relationships(filtered_tables[:20])
                
                # Count relationships per table
                table_relationship_count = {}
                for rel in sample_relationships:
                    table_relationship_count[rel['parent_table']] = table_relationship_count.get(rel['parent_table'], 0) + 1
                    table_relationship_count[rel['referenced_table']] = table_relationship_count.get(rel['referenced_table'], 0) + 1
                
                # Sort by relationship count and take top tables
                sorted_tables = sorted(filtered_tables, 
                                     key=lambda t: table_relationship_count.get(t, 0), 
                                     reverse=True)
                target_tables = sorted_tables[:max_tables]
            
            logger.info(f"Auto-discovered {len(filtered_tables)} tables, selected {len(target_tables)} for generation")
        else:
            target_tables = request.tables
            logger.info(f"Using specified tables: {target_tables}")
        
        if len(target_tables) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 tables are required for meaningful Q&A generation"
            )
        
        # Analyze database structure with better error handling
        try:
            # Get schemas with robust error handling
            schemas = {}
            accessible_tables = []
            
            for table_name in target_tables:
                try:
                    table_schemas = db_connector.get_table_schemas([table_name])
                    if table_name in table_schemas and table_schemas[table_name]:
                        schemas[table_name] = table_schemas[table_name]
                        accessible_tables.append(table_name)
                        logger.info(f"Successfully analyzed table '{table_name}' with {len(table_schemas[table_name])} columns")
                    else:
                        logger.warning(f"Skipping table '{table_name}' - no accessible columns found")
                except Exception as table_error:
                    logger.warning(f"Skipping problematic table '{table_name}': {table_error}")
                    continue
            
            if not schemas:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No accessible tables found among the specified tables. Please check table permissions and names."
                )
            
            if len(accessible_tables) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"At least 2 accessible tables are required. Only {len(accessible_tables)} tables are accessible: {accessible_tables}"
                )
            
            # Update target tables to only accessible ones
            target_tables = accessible_tables
            
            # Get relationships for accessible tables only
            relationships = db_connector.get_table_relationships(target_tables)
            
            logger.info(f"Analyzed {len(schemas)} accessible tables with {len(relationships)} relationships")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to analyze database structure: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database analysis failed: {str(e)}"
            )
        
        # Sample data from the primary table
        primary_table = target_tables[0]
        try:
            sample_data = db_connector.get_relational_sample(
                primary_table, target_tables, active_config.sample_size
            )
        except Exception as e:
            logger.error(f"Failed to sample data from tables: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data sampling failed: {str(e)}"
            )
        
        logger.info("Collected relational sample data")
        
        # Generate Q&A dataset
        try:
            from src.llm_generator import LLMGenerator
            
            # Update config for generation
            active_config.target_join_percentage = target_join_percentage
            active_config.min_questions = request.questions_per_table  # Use the requested number of questions
            
            llm_generator = LLMGenerator(active_config)
            qna_dataset, token_usage = llm_generator.generate_qna_dataset(
                schemas=schemas,
                relationships=relationships,
                sample_data=sample_data,
                table_names=target_tables
            )
            
        except Exception as e:
            logger.error(f"Q&A generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Q&A generation failed: {str(e)}"
            )
        
        # Calculate statistics
        join_questions = sum(
            1 for item in qna_dataset 
            if llm_generator.requires_join(item['question'], target_tables)
        )
        join_percentage = (join_questions / len(qna_dataset)) * 100 if qna_dataset else 0
        
        # Build response
        from api.models import QAPair, GenerationResponse
        qa_pairs = [QAPair(question=item['question'], expected_answer=item['expected_answer']) 
                    for item in qna_dataset]
        
        metadata = {
            'tables_analyzed': target_tables,
            'table_count': len(target_tables),
            'relationship_count': len(relationships),
            'sample_size': active_config.sample_size,
            'generation_timestamp': datetime.utcnow().isoformat()
        }
        
        statistics = {
            'total_questions': len(qna_dataset),
            'join_questions': join_questions,
            'join_percentage': round(join_percentage, 1),
            'single_table_questions': len(qna_dataset) - join_questions,
            'target_join_percentage': active_config.target_join_percentage,
            'meets_target': join_percentage >= active_config.target_join_percentage
        }
        
        logger.info(f"Generated {len(qna_dataset)} Q&A pairs ({join_percentage:.1f}% joins)")
        
        return GenerationResponse(
            success=True,
            message=f"Successfully generated {len(qna_dataset)} Q&A pairs",
            dataset=qa_pairs,
            metadata=metadata,
            statistics=statistics,
            token_usage=token_usage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset generation failed: {str(e)}"
        )


@app.post("/generate-async", response_model=AsyncJobResponse)
async def generate_dataset_async(request: GenerationRequest, background_tasks: BackgroundTasks):
    """
    Start asynchronous Q&A dataset generation.
    
    This endpoint starts a background job for dataset generation and returns a job ID
    that can be used to check status and retrieve results.
    """
    job_id = str(uuid.uuid4())
    
    # Initialize job
    job_storage[job_id] = {
        'id': job_id,
        'status': 'pending',
        'progress': 0.0,
        'result': None,
        'error': None,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # Start background task
    background_tasks.add_task(process_generation_job, job_id, request)
    
    logger.info(f"Started async generation job: {job_id}")
    
    return AsyncJobResponse(**job_storage[job_id])


@app.post("/api/generate/dataset-async", response_model=AsyncJobResponse)
async def api_generate_dataset_async(request: SimpleGenerationRequest, background_tasks: BackgroundTasks):
    """API endpoint for asynchronous Q&A dataset generation using environment configuration."""
    try:
        # Load configuration from environment
        config = Config()
        
        # Override database type if specified in request
        if request.db_type:
            config.db_type = request.db_type
        
        # Set difficulty level from request
        config.difficulty_level = request.difficulty_level
        
        # Check if database is configured
        if not config.is_database_configured():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database configuration not available. Please configure database settings first."
            )
        
        # Check if OpenAI is configured
        if not config.is_openai_configured():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI configuration not available. Please configure OpenAI API key first."
            )
        
        # Map difficulty level to target join percentage
        target_join_percentage = get_target_join_percentage(
            request.difficulty_level, 
            default_percentage=config.target_join_percentage
        )
        
        logger.info(f"Using difficulty level '{request.difficulty_level}' with {target_join_percentage}% target join percentage")
        
        # Create full generation request from simple request + environment config
        full_request = GenerationRequest(
            database_config=DatabaseConfig(
                server=config.db_server,
                database=config.db_database,
                username=config.db_username,
                password=config.db_password,
                driver=config.db_driver
            ),
            openai_config=OpenAIConfig(
                api_key=config.openai_api_key,
                model=config.openai_model
            ),
            generation_config=GenerationConfig(
                sample_size=config.sample_size,
                min_questions=request.questions_per_table,
                target_join_percentage=target_join_percentage,  # Use difficulty-based percentage
                max_tables=request.max_tables,  # Use max_tables from request instead of config
                output_file=request.output_file
            ),
            tables=request.tables,
            discover_all=False,
            exclude_tables=[]
        )
        
        return await generate_dataset_async(full_request, background_tasks)
        
    except Exception as e:
        logger.error(f"Async dataset generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Async dataset generation failed: {str(e)}"
        )


@app.get("/api/jobs")
async def list_jobs():
    """List all jobs."""
    jobs = []
    for job_id, job_data in job_storage.items():
        jobs.append({
            'id': job_id,
            'status': job_data.get('status', 'unknown'),
            'progress': job_data.get('progress', 0.0),
            'created_at': job_data.get('created_at'),
            'updated_at': job_data.get('updated_at'),
            'type': 'Dataset Generation'
        })
    return jobs

@app.get("/jobs/{job_id}", response_model=AsyncJobResponse)
async def get_job_status(job_id: str):
    """Get the status of an asynchronous job."""
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return AsyncJobResponse(**job_storage[job_id])

@app.get("/api/jobs/{job_id}")
async def get_job_status_api(job_id: str):
    """Get the status of an asynchronous job (API version)."""
    return await get_job_status(job_id)

@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job."""
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job = job_storage[job_id]
    if job['status'] in ['completed', 'failed']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job already finished"
        )
    
    job['status'] = 'cancelled'
    job['updated_at'] = datetime.utcnow().isoformat()
    
    return {"message": "Job cancelled successfully"}

@app.delete("/api/jobs/clear-completed")
async def clear_completed_jobs():
    """Clear all completed jobs."""
    completed_jobs = [job_id for job_id, job in job_storage.items() if job['status'] in ['completed', 'failed', 'cancelled']]
    for job_id in completed_jobs:
        del job_storage[job_id]
    
    return {"message": f"Cleared {len(completed_jobs)} completed jobs"}

@app.get("/api/jobs/{job_id}/download")
async def download_job_result(job_id: str):
    """Download the result of a completed job."""
    return await download_dataset(job_id)


@app.get("/download/{job_id}")
async def download_dataset(job_id: str):
    """Download the generated dataset as a JSON file."""
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job = job_storage[job_id]
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job not completed yet"
        )
    
    if not job['result'] or 'dataset' not in job['result']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset available for download"
        )
    
    # Create temporary file
    filename = f"qna_dataset_{job_id}.json"
    filepath = f"/tmp/{filename}"
    
    with open(filepath, 'w') as f:
        json.dump(job['result']['dataset'], f, indent=2)
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type='application/json'
    )


# Helper functions
async def discover_all_tables_async(db_connector: DatabaseConnector) -> List[str]:
    """Async wrapper for table discovery."""
    try:
        # Use the connector's get_all_tables method instead of direct connection
        tables = db_connector.get_all_tables()
        return tables
        
    except Exception as e:
        raise QNAGeneratorError(f"Failed to discover tables: {e}")


def generate_recommendations(tables: List[str], relationships: List[Dict], join_potential: float) -> List[str]:
    """Generate recommendations based on analysis."""
    recommendations = []
    
    if len(relationships) == 0:
        recommendations.append("No foreign key relationships found. Consider adding related tables for better join questions.")
    
    if len(tables) < 3:
        recommendations.append("Consider adding more related tables for richer Q&A scenarios.")
    
    if len(tables) > 8:
        recommendations.append("Large number of tables may produce complex questions. Consider reducing scope.")
    
    if join_potential < 40:
        recommendations.append(f"Join potential is {join_potential:.1f}%. Add more related tables to improve join question generation.")
    else:
        recommendations.append(f"Good join potential ({join_potential:.1f}%). Should generate quality relational questions.")
    
    recommendations.append("Review table relationships to ensure they make sense for your use case.")
    
    return recommendations


def suggest_optimal_tables(all_tables: List[str], relationships: List[Dict], max_tables: int) -> List[str]:
    """Suggest optimal table selection based on relationships."""
    if not relationships:
        return all_tables[:max_tables]
    
    # Find tables that are part of relationships
    related_tables = set()
    for rel in relationships:
        related_tables.add(rel['parent_table'])
        related_tables.add(rel['referenced_table'])
    
    # Prioritize tables with relationships
    suggested = list(related_tables)
    
    # Add remaining tables if needed
    for table in all_tables:
        if table not in suggested and len(suggested) < max_tables:
            suggested.append(table)
    
    return suggested[:max_tables]


async def process_generation_job(job_id: str, request: GenerationRequest):
    """Process generation job in background."""
    try:
        # Update job status
        job_storage[job_id].update({
            'status': 'running',
            'progress': 10.0,
            'updated_at': datetime.utcnow().isoformat()
        })
        
        # Run generation (this would be the same logic as generate_dataset)
        # For now, simulate the process
        await asyncio.sleep(2)  # Simulate work
        
        job_storage[job_id].update({
            'progress': 50.0,
            'updated_at': datetime.utcnow().isoformat()
        })
        
        # Here you would call the actual generation logic
        # result = await generate_dataset(request)
        
        await asyncio.sleep(3)  # Simulate more work
        
        # Update with completion
        job_storage[job_id].update({
            'status': 'completed',
            'progress': 100.0,
            'result': {'message': 'Generation completed successfully'},
            'updated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        job_storage[job_id].update({
            'status': 'failed',
            'error': str(e),
            'updated_at': datetime.utcnow().isoformat()
        })


# Configuration endpoints
@app.get("/api/config")
async def get_full_config():
    """Get current configuration including database and OpenAI settings."""
    try:
        if global_config is None:
            raise HTTPException(status_code=500, detail="Configuration not available")
        
        # Load both MySQL and SQL Server configurations from environment
        mysql_config = {
            "type": "mysql",
            "host": os.getenv("MYSQL_DB_SERVER", ""),
            "port": os.getenv("MYSQL_DB_PORT", "3306"),
            "database": os.getenv("MYSQL_DB_DATABASE", ""),
            "username": os.getenv("MYSQL_DB_USERNAME", ""),
            "password": os.getenv("MYSQL_DB_PASSWORD", ""),
            "driver": os.getenv("MYSQL_DB_DRIVER", "mysql+pymysql")
        }
        
        sqlserver_config = {
            "type": "sqlserver", 
            "host": os.getenv("SQLSERVER_DB_SERVER", ""),
            "port": os.getenv("SQLSERVER_DB_PORT", "1433"),
            "database": os.getenv("SQLSERVER_DB_DATABASE", ""),
            "username": os.getenv("SQLSERVER_DB_USERNAME", ""),
            "password": os.getenv("SQLSERVER_DB_PASSWORD", ""),
            "driver": os.getenv("SQLSERVER_DB_DRIVER", "ODBC Driver 17 for SQL Server")
        }
        
        return {
            "database_config": {
                "type": global_config.db_type,
                "host": global_config.db_server,
                "port": global_config.db_port,
                "database": global_config.db_database,
                "username": global_config.db_username,
                # Don't expose password
            },
            "mysql_config": mysql_config,
            "sqlserver_config": sqlserver_config,
            "openai_config": {
                "model": global_config.openai_model,
                "api_key_configured": bool(global_config.openai_api_key),
                "api_key_preview": f"{global_config.openai_api_key[:8]}..." if global_config.openai_api_key else None
            }
        }
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-openai")
async def test_openai_from_env():
    """Test OpenAI configuration from environment variables."""
    try:
        if global_config is None:
            raise HTTPException(status_code=500, detail="Configuration not available")
        
        if not global_config.is_openai_configured():
            return {
                "success": False,
                "message": "OpenAI not configured - check .env file",
                "configured": False
            }
        
        logger.info(f"Testing OpenAI connection with model {global_config.openai_model}")
        
        # Test OpenAI connection with a minimal API call
        from openai import OpenAI
        client = OpenAI(api_key=global_config.openai_api_key)
        
        # Make a minimal test call
        response = client.chat.completions.create(
            model=global_config.openai_model,
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1,
            temperature=0
        )
        
        return {
            "success": True,
            "message": "OpenAI connection successful",
            "model": global_config.openai_model,
            "configured": True,
            "test_response": response.choices[0].message.content if response.choices else "Test completed"
        }
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"OpenAI connection test failed: {error_message}")
        
        return {
            "success": False,
            "message": f"OpenAI connection failed: {error_message}",
            "configured": bool(global_config.openai_api_key) if global_config else False,
            "suggestions": [
                "Check if your OpenAI API key is correct in .env file",
                "Ensure the API key starts with 'sk-'",
                "Verify you have sufficient API credits",
                "Check your internet connection"
            ]
        }

@app.get("/api/config/database")
async def get_database_config():
    """Get current database configuration (with masked password)."""
    try:
        if global_config is None:
            raise HTTPException(status_code=500, detail="Configuration not available")
        return global_config.get_database_config()
    except Exception as e:
        logger.error(f"Failed to get database config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/database")
async def update_database_config(config: DatabaseConfig):
    """Update database configuration."""
    try:
        if global_config is None:
            raise HTTPException(status_code=500, detail="Configuration not available")
        
        # Update global config
        config_dict = config.model_dump()
        global_config.update_database_config(config_dict)
        
        return {"message": "Database configuration updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update database config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/openai")
async def get_openai_config():
    """Get OpenAI configuration info (without exposing API key)."""
    try:
        if global_config is None:
            raise HTTPException(status_code=500, detail="Configuration not available")
        return global_config.get_openai_config()
    except Exception as e:
        logger.error(f"Failed to get OpenAI config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Connection Management Endpoints
@app.post("/api/connection/start")
async def start_database_connection(request: dict):
    """Start and maintain an active database connection."""
    try:
        # Extract database config from request
        db_config_data = request.get('database_config')
        if not db_config_data:
            raise HTTPException(status_code=400, detail="Missing database_config in request")
        
        # Create DatabaseConfig object
        db_config = DatabaseConfig(**db_config_data)
        
        # Create configuration from request
        config = create_config_from_request(db_config)
        
        logger.info(f"Starting {config.db_type} database connection to {config.db_server}")
        
        # Start the connection
        success, message = config.start_connection()
        
        if success:
            connection_info = config.get_active_connection_info()
            return {
                "success": True,
                "message": message,
                "connection": connection_info
            }
        else:
            raise HTTPException(status_code=400, detail={
                "success": False,
                "message": message
            })
            
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to start connection: {e}")
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": f"Failed to start connection: {str(e)}"
        })


@app.post("/api/connection/stop")
async def stop_database_connection():
    """Stop the currently active database connection."""
    try:
        from src.config import Config
        
        success, message = Config().stop_active_connection()
        
        return {
            "success": success,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Failed to stop connection: {e}")
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": f"Failed to stop connection: {str(e)}"
        })


@app.get("/api/connection/status")
async def get_connection_status():
    """Get the status of active database connections."""
    try:
        from src.config import Config
        
        connection_info = Config.get_active_connection_info()
        
        return {
            "has_active_connection": Config.has_active_connection(),
            "connection": connection_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get connection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/dataset-demo", response_model=GenerationResponse)
async def generate_dataset_demo(request: SimpleGenerationRequest):
    """Demo endpoint for Q&A dataset generation using mock data (no database required)."""
    try:
        logger.info("Using demo mode - no database connection required")
        
        # Load configuration from environment (only need OpenAI)
        config = Config()
        
        # Override database type if specified in request (though not used in demo)
        if request.db_type:
            config.db_type = request.db_type
        
        # Set difficulty level from request
        config.difficulty_level = request.difficulty_level
        
        # Check if OpenAI is configured
        if not config.is_openai_configured():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI configuration not available. Please configure OpenAI API key first."
            )
        
        # Use demo data
        schemas = DEMO_TABLES
        relationships = DEMO_RELATIONSHIPS
        sample_data = DEMO_SAMPLE_DATA
        table_names = list(DEMO_TABLES.keys())
        
        logger.info(f"Using demo tables: {table_names}")
        
        # Map difficulty level to target join percentage
        target_join_percentage = get_target_join_percentage(
            request.difficulty_level, 
            default_percentage=config.target_join_percentage
        )
        
        # Update config with difficulty-based join percentage and question count
        config.target_join_percentage = target_join_percentage
        config.min_questions = request.questions_per_table  # Use the requested number of questions
        
        logger.info(f"Using difficulty level '{request.difficulty_level}' with {target_join_percentage}% target join percentage")
        
        # Initialize LLM generator
        llm_generator = LLMGenerator(config)
        
        # Generate Q&A dataset with demo data
        qna_dataset, token_usage = llm_generator.generate_qna_dataset(
            schemas=schemas,
            relationships=relationships,
            sample_data=sample_data,
            table_names=table_names
        )
        
        # Calculate statistics
        join_questions = sum(
            1 for item in qna_dataset 
            if llm_generator.requires_join(item['question'], table_names)
        )
        join_percentage = (join_questions / len(qna_dataset)) * 100 if qna_dataset else 0
        
        # Build response
        qa_pairs = [QAPair(question=item['question'], expected_answer=item['expected_answer']) 
                    for item in qna_dataset]
        
        metadata = {
            'tables_analyzed': table_names,
            'table_count': len(table_names),
            'relationship_count': len(relationships),
            'sample_size': len(sample_data.get(table_names[0], [])),
            'generation_timestamp': datetime.utcnow().isoformat(),
            'demo_mode': True
        }
        
        statistics = {
            'total_questions': len(qna_dataset),
            'join_questions': join_questions,
            'join_percentage': round(join_percentage, 1),
            'single_table_questions': len(qna_dataset) - join_questions,
            'target_join_percentage': config.target_join_percentage,
            'meets_target': join_percentage >= config.target_join_percentage
        }
        
        logger.info(f"Demo generation completed: {len(qna_dataset)} Q&A pairs ({join_percentage:.1f}% joins)")
        
        return GenerationResponse(
            success=True,
            message=f"Successfully generated {len(qna_dataset)} Q&A pairs using demo data",
            dataset=qa_pairs,
            metadata=metadata,
            statistics=statistics,
            token_usage=token_usage
        )
        
    except Exception as e:
        logger.error(f"Demo dataset generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo dataset generation failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
