#!/usr/bin/env python3
"""
GenAI SQL Test Data Generator

A backend tool that connects to SQL Server databases, discovers table schemas 
and relationships, and leverages LLM to generate test datasets of questions 
and answers with emphasis on queries requiring table joins.

Usage:
    python generate_dataset.py --tables Employees,Departments
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import click
import coloredlogs
from dotenv import load_dotenv

from src.database_factory import DatabaseConnectorFactory
from src.llm_generator import LLMGenerator
from src.config import Config
from src.exceptions import QNAGeneratorError


# Configure logging
def setup_logging(log_level: str = "INFO"):
    """Setup colored logging with specified level."""
    coloredlogs.install(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        field_styles={
            'asctime': {'color': 'green'},
            'levelname': {'bold': True},
            'name': {'color': 'blue'}
        }
    )


@click.command()
@click.option(
    '--tables', 
    required=False,
    help='Comma-separated list of table names to analyze (minimum 2 tables). Use --discover-all to auto-discover.'
)
@click.option(
    '--discover-all',
    is_flag=True,
    help='Automatically discover and analyze all tables in the database (limited to first 10)'
)
@click.option(
    '--output',
    default=None,
    help='Output file path (defaults to qna_dataset.json)'
)
@click.option(
    '--sample-size',
    type=int,
    default=None,
    help='Number of sample rows to fetch from primary table'
)
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
    default=None,
    help='Set logging level'
)
def main(tables: str, discover_all: bool, output: str, sample_size: int, log_level: str):
    """
    GenAI SQL Test Data Generator CLI
    
    Generates Q&A test datasets from SQL Server database schemas and relationships.
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        config = Config()
        
        # Override config with CLI arguments if provided
        if output:
            config.output_file = output
        if sample_size:
            config.sample_size = sample_size
        if log_level:
            config.log_level = log_level
        
        # Setup logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting GenAI SQL Test Data Generator")
        
        # Determine table list
        if discover_all:
            logger.info("Auto-discovering all database tables...")
            # Import here to avoid circular imports
            from discover_database import discover_all_tables
            db_connector_temp = DatabaseConnectorFactory.create_connector(config)
            all_tables = discover_all_tables(db_connector_temp)
            table_list = all_tables[:10]  # Limit to first 10 to avoid overwhelming LLM
            logger.info(f"Auto-discovered tables: {table_list}")
        elif tables:
            table_list = [table.strip() for table in tables.split(',')]
            logger.info(f"User-specified tables: {table_list}")
        else:
            raise QNAGeneratorError("Either --tables or --discover-all must be specified")
        
        # Validate minimum table count
        if len(table_list) < 2:
            raise QNAGeneratorError("At least 2 tables are required for generating join-based questions")
        
        logger.info(f"Processing {len(table_list)} tables: {table_list}")
        
        # Initialize database connector
        db_connector = DatabaseConnectorFactory.create_connector(config)
        
        # Test database connection
        logger.info("Testing database connection...")
        if not db_connector.test_connection():
            raise QNAGeneratorError("Failed to connect to database")
        
        logger.info("Database connection successful")
        
        # Discover schemas and relationships
        logger.info("Discovering table schemas and relationships...")
        schemas = db_connector.get_table_schemas(table_list)
        relationships = db_connector.get_table_relationships(table_list)
        
        logger.info(f"Discovered schemas for {len(schemas)} tables")
        logger.info(f"Found {len(relationships)} foreign key relationships")
        
        # Perform relational data sampling
        logger.info("Performing relational data sampling...")
        primary_table = table_list[0]  # Use first table as primary
        sample_data = db_connector.get_relational_sample(
            primary_table, 
            table_list, 
            config.sample_size
        )
        
        logger.info(f"Collected sample data from {len(sample_data)} tables")
        
        # Initialize LLM generator
        llm_generator = LLMGenerator(config)
        
        # Generate Q&A dataset
        logger.info("Generating Q&A dataset using LLM...")
        qna_dataset = llm_generator.generate_qna_dataset(
            schemas=schemas,
            relationships=relationships,
            sample_data=sample_data,
            table_names=table_list
        )
        
        logger.info(f"Generated {len(qna_dataset)} question-answer pairs")
        
        # Validate dataset quality
        join_questions = sum(1 for item in qna_dataset if llm_generator.requires_join(item['question'], table_list))
        join_percentage = (join_questions / len(qna_dataset)) * 100
        
        logger.info(f"Questions requiring joins: {join_questions}/{len(qna_dataset)} ({join_percentage:.1f}%)")
        
        if join_percentage < config.target_join_percentage:
            logger.warning(f"Join percentage ({join_percentage:.1f}%) below target ({config.target_join_percentage}%)")
        
        # Save output
        output_path = Path(config.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(qna_dataset, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dataset saved to: {output_path.absolute()}")
        
        # Print summary
        click.echo("\n" + "="*50)
        click.echo("GENERATION COMPLETE")
        click.echo("="*50)
        click.echo(f"Tables processed: {len(table_list)}")
        click.echo(f"Questions generated: {len(qna_dataset)}")
        click.echo(f"Join questions: {join_questions} ({join_percentage:.1f}%)")
        click.echo(f"Output file: {output_path.absolute()}")
        click.echo("="*50)
        
        return 0
        
    except QNAGeneratorError as e:
        logger.error(f"Application error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug("Stack trace:", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
