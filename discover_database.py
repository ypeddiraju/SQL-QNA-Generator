#!/usr/bin/env python3
"""
Database Discovery Tool for GenAI SQL Test Data Generator

This tool helps you discover all tables in your database and understand
their relationships before running the main generator.
"""

import logging
import sys
from typing import List, Dict, Any

import click
import coloredlogs
from dotenv import load_dotenv
from tabulate import tabulate

from src.database_factory import DatabaseConnectorFactory
from src.database_base import DatabaseConnectorBase
from src.config import Config
from src.exceptions import QNAGeneratorError


def setup_logging(log_level: str = "INFO"):
    """Setup colored logging with specified level."""
    coloredlogs.install(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@click.command()
@click.option(
    '--analyze-all',
    is_flag=True,
    help='Analyze all tables in the database'
)
@click.option(
    '--min-tables',
    type=int,
    default=2,
    help='Minimum number of tables to include in analysis (default: 2)'
)
@click.option(
    '--max-tables',
    type=int,
    default=10,
    help='Maximum number of tables to include to avoid overwhelming LLM (default: 10)'
)
@click.option(
    '--exclude-tables',
    default='',
    help='Comma-separated list of table names to exclude (e.g., "sys,log,temp")'
)
@click.option(
    '--generate-dataset',
    is_flag=True,
    help='Automatically generate dataset after discovery'
)
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
    default='INFO',
    help='Set logging level'
)
def discover_database(analyze_all: bool, min_tables: int, max_tables: int, 
                     exclude_tables: str, generate_dataset: bool, log_level: str):
    """
    Discover and analyze database structure for Q&A generation.
    
    This tool helps you understand your database before running the main generator.
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Setup logging
        setup_logging(log_level)
        logger = logging.getLogger(__name__)
        
        # Initialize configuration
        config = Config()
        
        # Initialize database connector
        db_connector = DatabaseConnectorFactory.create_connector(config)
        
        # Test database connection
        logger.info("Connecting to database...")
        if not db_connector.test_connection():
            raise QNAGeneratorError("Failed to connect to database")
        
        click.echo("🎯 Database Discovery Tool")
        click.echo("=" * 50)
        
        # Discover all tables
        click.echo("\n📊 Discovering all tables...")
        all_tables = discover_all_tables(db_connector)
        
        if not all_tables:
            click.echo("❌ No tables found in database")
            return 1
        
        click.echo(f"✅ Found {len(all_tables)} tables total")
        
        # Apply filters
        excluded = [t.strip() for t in exclude_tables.split(',') if t.strip()]
        filtered_tables = [t for t in all_tables if not any(exc.lower() in t.lower() for exc in excluded)]
        
        if analyze_all:
            target_tables = filtered_tables[:max_tables]  # Limit to prevent overwhelming LLM
        else:
            # Interactive selection
            target_tables = interactive_table_selection(filtered_tables, min_tables, max_tables)
        
        if len(target_tables) < min_tables:
            click.echo(f"❌ Need at least {min_tables} tables for meaningful Q&A generation")
            return 1
        
        # Analyze selected tables
        click.echo(f"\n🔍 Analyzing {len(target_tables)} selected tables...")
        analysis = analyze_selected_tables(db_connector, target_tables)
        
        # Display analysis results
        display_analysis_results(analysis)
        
        # Generate dataset if requested
        if generate_dataset:
            click.echo("\n🤖 Generating Q&A dataset...")
            generate_command = f"python generate_dataset.py --tables \"{','.join(target_tables)}\""
            click.echo(f"Running: {generate_command}")
            
            import subprocess
            result = subprocess.run(generate_command, shell=True)
            return result.returncode
        else:
            # Show command to run
            click.echo("\n🚀 Ready to Generate!")
            click.echo("=" * 50)
            click.echo("Run this command to generate your Q&A dataset:")
            click.echo()
            click.echo(f"python generate_dataset.py --tables \"{','.join(target_tables)}\"")
            click.echo()
        
        return 0
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return 1


def discover_all_tables(db_connector: DatabaseConnectorBase) -> List[str]:
    """Discover all user tables in the database."""
    try:
        # Use the database connector's built-in method instead of direct connection
        tables = db_connector.get_all_tables()
        return tables
            
    except Exception as e:
        raise QNAGeneratorError(f"Failed to discover tables: {e}")


def interactive_table_selection(all_tables: List[str], min_tables: int, max_tables: int) -> List[str]:
    """Interactive table selection interface."""
    click.echo("\n📋 Available Tables:")
    click.echo("-" * 30)
    
    # Display tables in a nice format
    table_data = []
    for i, table in enumerate(all_tables, 1):
        table_data.append([i, table])
    
    click.echo(tabulate(table_data, headers=["#", "Table Name"], tablefmt="grid"))
    
    click.echo(f"\nSelect {min_tables}-{max_tables} tables for analysis:")
    click.echo("Enter table numbers separated by commas (e.g., 1,3,5)")
    click.echo("Or enter 'all' to select all tables (limited to first 10)")
    
    while True:
        selection = click.prompt("Your selection", type=str)
        
        if selection.lower() == 'all':
            return all_tables[:max_tables]
        
        try:
            # Parse comma-separated numbers
            indices = [int(x.strip()) for x in selection.split(',')]
            
            # Validate indices
            if not all(1 <= i <= len(all_tables) for i in indices):
                click.echo(f"❌ Invalid selection. Use numbers 1-{len(all_tables)}")
                continue
            
            if len(indices) < min_tables:
                click.echo(f"❌ Select at least {min_tables} tables")
                continue
                
            if len(indices) > max_tables:
                click.echo(f"❌ Select at most {max_tables} tables to avoid overwhelming the LLM")
                continue
            
            # Convert to table names
            selected_tables = [all_tables[i-1] for i in indices]
            return selected_tables
            
        except ValueError:
            click.echo("❌ Invalid input. Enter numbers separated by commas")


def analyze_selected_tables(db_connector: DatabaseConnectorBase, tables: List[str]) -> Dict[str, Any]:
    """Analyze the selected tables and their relationships."""
    
    # Get schemas
    schemas = db_connector.get_table_schemas(tables)
    
    # Get relationships
    relationships = db_connector.get_table_relationships(tables)
    
    # Sample data from first table to get an idea of data volume
    sample_data = {}
    if tables:
        try:
            sample_data = db_connector.get_relational_sample(tables[0], tables, 3)  # Small sample for analysis
        except Exception as e:
            print(f"Warning: Could not sample data: {e}")
    
    return {
        'tables': tables,
        'schemas': schemas,
        'relationships': relationships,
        'sample_data': sample_data
    }


def display_analysis_results(analysis: Dict[str, Any]):
    """Display the analysis results in a user-friendly format."""
    
    click.echo("\n📊 Database Analysis Results")
    click.echo("=" * 50)
    
    # Table summary
    click.echo(f"\n🗂️  Selected Tables ({len(analysis['tables'])}):")
    for table in analysis['tables']:
        column_count = len(analysis['schemas'].get(table, []))
        click.echo(f"  • {table} ({column_count} columns)")
    
    # Relationships summary
    relationships = analysis['relationships']
    if relationships:
        click.echo(f"\n🔗 Foreign Key Relationships ({len(relationships)}):")
        for rel in relationships:
            click.echo(f"  • {rel['parent_table']}.{rel['parent_column']} → {rel['referenced_table']}.{rel['referenced_column']}")
        
        # Calculate join potential
        join_percentage = min(100, (len(relationships) / len(analysis['tables'])) * 100)
        if join_percentage >= 40:
            click.echo(f"  ✅ Good join potential ({join_percentage:.0f}%)")
        else:
            click.echo(f"  ⚠️  Limited join potential ({join_percentage:.0f}%) - may need more related tables")
    else:
        click.echo("\n🔗 Foreign Key Relationships:")
        click.echo("  ❌ No foreign key relationships found")
        click.echo("  ⚠️  Q&A generation will focus on single-table queries")
    
    # Data sample summary
    sample_data = analysis['sample_data']
    if sample_data:
        click.echo(f"\n📈 Data Sample Summary:")
        total_rows = sum(len(rows) for rows in sample_data.values())
        click.echo(f"  • Total sample rows: {total_rows}")
        for table, rows in sample_data.items():
            click.echo(f"  • {table}: {len(rows)} rows")
    
    # Recommendations
    click.echo(f"\n💡 Recommendations:")
    if len(relationships) == 0:
        click.echo("  • Consider adding related tables with foreign keys for better join questions")
    if len(analysis['tables']) < 3:
        click.echo("  • Consider adding more related tables for richer Q&A scenarios")
    if len(analysis['tables']) > 8:
        click.echo("  • Large number of tables may produce complex questions - consider reducing scope")
    
    click.echo("  • Review the relationships above to ensure they make sense for your use case")
    click.echo("  • The generator will create ~40% join-based questions and 60% single-table questions")


if __name__ == '__main__':
    sys.exit(discover_database())
