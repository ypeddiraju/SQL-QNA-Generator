"""
Tests for LLM generator module.
"""

import pytest
import json
from unittest.mock import Mock, patch

from src.llm_generator import LLMGenerator
from src.exceptions import LLMGenerationError, ValidationError


class TestLLMGenerator:
    """Test cases for LLMGenerator class."""
    
    def test_init(self, mock_config):
        """Test LLMGenerator initialization."""
        generator = LLMGenerator(mock_config)
        assert generator.config == mock_config
        assert generator.llm is not None
    
    def test_requires_join_multiple_tables(self):
        """Test join detection with multiple table references."""
        generator = LLMGenerator(Mock())
        
        question = "How many employees work in the Sales department?"
        table_names = ["Employees", "Departments"]
        
        result = generator.requires_join(question, table_names)
        assert result is True
    
    def test_requires_join_single_table(self):
        """Test join detection with single table reference."""
        generator = LLMGenerator(Mock())
        
        question = "How many employees are there?"
        table_names = ["Employees", "Departments"]
        
        result = generator.requires_join(question, table_names)
        assert result is False
    
    def test_requires_join_keywords(self):
        """Test join detection using keywords."""
        generator = LLMGenerator(Mock())
        
        question = "List employees who work in New York"
        table_names = ["Employees", "Departments"]
        
        result = generator.requires_join(question, table_names)
        assert result is True
    
    def test_build_database_context(self, mock_config, sample_schemas, sample_relationships, sample_data):
        """Test database context building."""
        generator = LLMGenerator(mock_config)
        
        context = generator._build_database_context(
            sample_schemas, sample_relationships, sample_data, ['Employees', 'Departments']
        )
        
        assert "=== DATABASE SCHEMAS ===" in context
        assert "=== TABLE RELATIONSHIPS ===" in context  
        assert "=== SAMPLE DATA ===" in context
        assert "Employees" in context
        assert "Departments" in context
        assert "John Smith" in context
    
    def test_parse_llm_response_valid_json(self):
        """Test parsing valid JSON response."""
        generator = LLMGenerator(Mock())
        
        response = '''[
            {"question": "Test question?", "expected_answer": "Test answer"},
            {"question": "Another question?", "expected_answer": "Another answer"}
        ]'''
        
        result = generator._parse_llm_response(response)
        
        assert len(result) == 2
        assert result[0]['question'] == "Test question?"
        assert result[0]['expected_answer'] == "Test answer"
    
    def test_parse_llm_response_with_markdown(self):
        """Test parsing JSON response wrapped in markdown."""
        generator = LLMGenerator(Mock())
        
        response = '''```json
        [
            {"question": "Test question?", "expected_answer": "Test answer"}
        ]
        ```'''
        
        result = generator._parse_llm_response(response)
        
        assert len(result) == 1
        assert result[0]['question'] == "Test question?"
    
    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        generator = LLMGenerator(Mock())
        
        response = "This is not valid JSON"
        
        with pytest.raises(ValidationError):
            generator._parse_llm_response(response)
    
    def test_validate_dataset_success(self, mock_config):
        """Test successful dataset validation."""
        mock_config.min_questions = 2
        mock_config.target_join_percentage = 50
        
        generator = LLMGenerator(mock_config)
        
        dataset = [
            {"question": "How many employees in Sales?", "expected_answer": "5"},
            {"question": "List all employees", "expected_answer": "10"}
        ]
        
        # Should not raise exception
        generator._validate_dataset(dataset, ["Employees", "Departments"])
    
    def test_validate_dataset_insufficient_questions(self, mock_config):
        """Test dataset validation with insufficient questions."""
        mock_config.min_questions = 10
        
        generator = LLMGenerator(mock_config)
        
        dataset = [
            {"question": "Test question?", "expected_answer": "Test answer"}
        ]
        
        with pytest.raises(ValidationError):
            generator._validate_dataset(dataset, ["Employees", "Departments"])
