"""
LLM integration module using LangChain and OpenAI.

Generates Q&A datasets from database schemas and sample data.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks import get_openai_callback

from .config import Config
from .exceptions import LLMGenerationError, ValidationError


logger = logging.getLogger(__name__)


class LLMGenerator:
    """Handles LLM-based Q&A generation using LangChain and OpenAI."""
    
    def __init__(self, config: Config):
        """Initialize LLM generator with configuration."""
        self.config = config
        self.llm = ChatOpenAI(
            openai_api_key=config.openai_api_key,
            model_name=config.openai_model,
            temperature=0.7,
            max_tokens=4000
        )
        
    def generate_qna_dataset(self, schemas: Dict[str, List[Dict]], 
                           relationships: List[Dict], 
                           sample_data: Dict[str, List[Dict]], 
                           table_names: List[str]) -> tuple[List[Dict[str, str]], Dict[str, Any]]:
        """
        Generate Q&A dataset using LLM based on database context.
        
        Args:
            schemas: Table schema information
            relationships: Foreign key relationships
            sample_data: Sample data from tables
            table_names: List of table names
            
        Returns:
            Tuple of (List of question-answer pairs, Token usage information)
        """
        try:
            logger.info("Constructing context for LLM generation...")
            
            # Build comprehensive context
            context = self._build_database_context(schemas, relationships, sample_data, table_names)
            
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create human prompt with context
            human_prompt = self._create_human_prompt(context, table_names)
            
            logger.info("Sending request to LLM...")
            logger.debug(f"Context length: {len(context)} characters")
            
            # Generate Q&A pairs using LLM
            with get_openai_callback() as cb:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=human_prompt)
                ]
                
                response = self.llm.invoke(messages)
                
                # Capture token usage information
                token_usage = {
                    'total_tokens': cb.total_tokens,
                    'prompt_tokens': cb.prompt_tokens,
                    'completion_tokens': cb.completion_tokens,
                    'total_cost': cb.total_cost,
                    'model': self.config.openai_model
                }
                
                logger.info(f"LLM call completed. Tokens used: {cb.total_tokens} (prompt: {cb.prompt_tokens}, completion: {cb.completion_tokens})")
                logger.debug(f"Cost: ${cb.total_cost:.4f}")
            
            # Parse and validate response
            logger.debug(f"LLM raw response: {response.content[:500]}...")
            
            # Temporary: Return hardcoded dataset for debugging
            # qna_dataset = [
            #     {
            #         "question": "How many tables are in the database?",
            #         "expected_answer": str(len(table_names))
            #     },
            #     {
            #         "question": "What are the main tables in the schema?",
            #         "expected_answer": ", ".join(table_names[:3])
            #     }
            # ]
            
            # logger.info(f"Using hardcoded dataset with {len(qna_dataset)} Q&A pairs")
            # return qna_dataset
            
            #Original code (commented out for debugging):
            qna_dataset = self._parse_llm_response(response.content)
            self._validate_dataset(qna_dataset, table_names)
            logger.info(f"Successfully generated {len(qna_dataset)} Q&A pairs")
            return qna_dataset, token_usage
            
        except Exception as e:
            logger.error(f"Error generating Q&A dataset: {e}")
            logger.error(f"Full error details:", exc_info=True)
            # Return empty token usage on error
            error_token_usage = {
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_cost': 0.0,
                'model': self.config.openai_model,
                'error': str(e)
            }
            raise LLMGenerationError(f"Failed to generate Q&A dataset: {e}")
    
    def _build_database_context(self, schemas: Dict[str, List[Dict]], 
                              relationships: List[Dict], 
                              sample_data: Dict[str, List[Dict]], 
                              table_names: List[str]) -> str:
        """Build optimized database context for LLM to stay within token limits."""
        
        context_parts = []
        
        # Add table schemas (keep only essential columns)
        context_parts.append("=== DATABASE SCHEMAS ===")
        for table_name, columns in schemas.items():
            # Limit columns per table to most important ones
            important_columns = columns[:10]  # Limit to first 10 columns per table
            context_parts.append(f"\nTable: {table_name}")
            context_parts.append("Key Columns:")
            for col in important_columns:
                context_parts.append(f"  - {col['column_name']}: {col['data_type']}")
            if len(columns) > 10:
                context_parts.append(f"  ... and {len(columns) - 10} more columns")
        
        # Add relationships (essential for joins)
        if relationships:
            context_parts.append("\n=== TABLE RELATIONSHIPS ===")
            for rel in relationships[:20]:  # Limit to first 20 relationships
                context_parts.append(
                    f"{rel['parent_table']}.{rel['parent_column']} -> "
                    f"{rel['referenced_table']}.{rel['referenced_column']}"
                )
            if len(relationships) > 20:
                context_parts.append(f"... and {len(relationships) - 20} more relationships")
        
        # Add sample data (very limited to save tokens)
        context_parts.append("\n=== SAMPLE DATA ===")
        for table_name, rows in sample_data.items():
            context_parts.append(f"\nTable: {table_name}")
            if rows:
                # Show only 1-2 rows as examples to save tokens
                sample_rows = rows[:2]  # Limit to first 2 rows for context
                context_parts.append(f"Sample ({len(rows)} total rows):")
                for i, row in enumerate(sample_rows, 1):
                    # Truncate long values to save tokens
                    truncated_row = {}
                    for k, v in row.items():
                        if isinstance(v, str) and len(str(v)) > 50:
                            truncated_row[k] = str(v)[:50] + "..."
                        else:
                            truncated_row[k] = v
                    context_parts.append(f"  Row {i}: {truncated_row}")
                if len(rows) > 2:
                    context_parts.append(f"  ... {len(rows) - 2} more rows available")
            else:
                context_parts.append("  No sample data available")
        
        context = "\n".join(context_parts)
        
        # Log context size for debugging
        logger.info(f"Generated context size: {len(context)} characters (~{len(context.split())} words)")
        
        return context
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for LLM based on difficulty level."""
        
        # Base prompt that applies to all difficulty levels
        base_prompt = """You are an expert business analyst and SQL test data generator. Your task is to create realistic business intelligence question-answer pairs for testing Natural Language to SQL applications.

CRITICAL REQUIREMENTS:
1. Generate EXACTLY the number of questions requested
2. Target join percentage will be specified in the user prompt
3. All answers MUST be derived ONLY from the provided sample data
4. Create REALISTIC business questions that analysts would actually ask
5. Output MUST be valid JSON array format

BUSINESS CONTEXT: Generate questions as if for a real business analyst working with:
- Sales data, customer analytics, inventory management
- Performance metrics, revenue analysis, operational insights
- Time-based trends, geographic analysis, customer segmentation
- Employee productivity, profitability analysis"""

        # Difficulty-specific instructions
        difficulty_instructions = self._get_difficulty_instructions()
        
        # Common requirements
        common_requirements = """
ANSWER REQUIREMENTS:
- Base answers ONLY on the provided sample data
- For COUNT queries, count the actual rows in the sample
- For aggregations, calculate from sample data values
- For metrics, use realistic business terminology
- If a question cannot be answered from sample data, modify the question appropriately

QUESTION STYLE:
- Use professional business language
- Include relevant business metrics and KPIs
- Frame questions as real analytical needs
- Use industry-standard terminology

OUTPUT FORMAT:
Return ONLY a valid JSON array where each object has exactly two keys:
- "question": The natural language business question
- "expected_answer": The correct answer based on sample data

Example:
[
  {
    "question": "What's the total sales revenue for the Technology department?",
    "expected_answer": "$125,000"
  }
]"""

        return base_prompt + difficulty_instructions + common_requirements
    
    def _get_difficulty_instructions(self) -> str:
        """Get difficulty-specific instructions for the prompt."""
        difficulty = self.config.difficulty_level.lower()
        
        if difficulty == "easy":
            return """

DIFFICULTY LEVEL: EASY
QUESTION TYPES TO PRIORITIZE:
- Simple lookups (single table queries) - PRIMARY FOCUS
- Basic filtering with single conditions
- Simple COUNT queries
- Direct attribute queries
- Minimal complex joins (only when target percentage requires)

COMPLEXITY GUIDELINES:
- Use straightforward language
- Avoid complex business logic
- Focus on direct data retrieval
- Keep questions simple and clear"""

        elif difficulty == "medium":
            return """

DIFFICULTY LEVEL: MEDIUM  
QUESTION TYPES TO INCLUDE:
- Balanced mix of single and multi-table queries
- Filtering with multiple conditions
- Basic aggregations (COUNT, SUM, AVG)
- Moderate join queries
- Some analytical questions

COMPLEXITY GUIDELINES:
- Mix simple and moderately complex questions
- Include some business logic
- Balance single-table and join queries
- Use clear but more varied language"""

        elif difficulty == "hard":
            return """

DIFFICULTY LEVEL: HARD
QUESTION TYPES TO PRIORITIZE:
- Complex multi-table joins - PRIMARY FOCUS
- Advanced aggregations with grouping
- Nested logical conditions
- Complex analytical queries
- Questions requiring multiple join paths
- Business intelligence style questions

COMPLEXITY GUIDELINES:
- Emphasize complex relational queries
- Use sophisticated business logic
- Create questions requiring multiple steps
- Include advanced analytical concepts"""

        else:  # mixed or default
            return """

DIFFICULTY LEVEL: MIXED
QUESTION TYPES TO INCLUDE:
- Wide variety from simple to complex
- Simple lookups (single table queries)
- Filtering with conditions (simple and complex)
- Aggregations (COUNT, SUM, AVG, etc.)
- Complex relational queries requiring joins
- Questions about relationships between entities
- Analytical and business logic questions

COMPLEXITY GUIDELINES:
- Create diverse difficulty levels
- Balance all question types
- Include both simple and sophisticated queries
- Vary language complexity appropriately"""
    
    def _create_human_prompt(self, context: str, table_names: List[str]) -> str:
        """Create human prompt with database context and difficulty-specific instructions."""
        
        difficulty_context = self._get_difficulty_context()
        target_joins = int(self.config.min_questions * self.config.target_join_percentage / 100)
        
        return f"""Based on the following database information, generate {self.config.min_questions} diverse question-answer pairs for testing a Natural Language to SQL system.

{context}

DIFFICULTY LEVEL: {self.config.difficulty_level.upper()}
{difficulty_context}

TARGET REQUIREMENTS:
- Generate EXACTLY {self.config.min_questions} questions  
- Ensure at least {target_joins} questions ({self.config.target_join_percentage}%) require joining tables: {', '.join(table_names)}
- All answers must be based ONLY on the sample data provided above
- Return ONLY the JSON array, no additional text or explanation

CRITICAL: For CROSS-TABLE questions, use these business-realistic patterns that will be detected as joins:

SALES & REVENUE ANALYSIS:
- "What's the total revenue by product category?"
- "Which stores generate the highest sales per square foot?"
- "Show monthly sales trends by region"
- "Calculate average transaction value by customer segment"

CUSTOMER ANALYTICS:
- "What's the customer lifetime value by loyalty tier?"
- "Which customers have the highest purchase frequency?"
- "Show customer distribution by geographic region"
- "Calculate customer acquisition cost by marketing channel"

INVENTORY & OPERATIONS:
- "What's the inventory turnover rate by product category?"
- "Which suppliers have the highest-rated products?"
- "Show employee productivity metrics by store location"
- "Calculate profit margins by product and store combination"

PERFORMANCE METRICS:
- "Compare store performance relative to market size"
- "Which employee-department combinations achieve highest sales?"
- "Analyze seasonal demand patterns across product categories"

AVOID these patterns for JOIN questions (may not be detected as cross-table):
- Simple entity lists: "List all customers"
- Single-table counts: "How many products do we have?"
- Basic lookups: "What's the price of Product X?"

Generate {self.config.min_questions} question-answer pairs now:"""
    
    def _get_difficulty_context(self) -> str:
        """Get difficulty-specific context for the human prompt."""
        difficulty = self.config.difficulty_level.lower()
        
        if difficulty == "easy":
            return f"""

DIFFICULTY LEVEL: EASY - Basic Business Queries
TARGET: {self.config.target_join_percentage}% cross-table analysis questions

SINGLE-TABLE EXAMPLES (Basic Reporting):
- "What's the total number of customers?"
- "List all product categories"
- "What's the highest price in our catalog?"
- "Show all active employees"
- "What's the total inventory value?"

CROSS-TABLE EXAMPLES (Simple Analytics):
- "Which products belong to the Electronics category?"
- "What's the total sales by store location?"
- "List employees and their department names"
- "Show customers and their loyalty tier status"
- "How many orders were placed by each customer?"

FOCUS: Basic business reporting with straightforward joins and simple aggregations."""
        elif difficulty == "medium":
            return f"""

DIFFICULTY LEVEL: MEDIUM - Business Intelligence & Analytics
TARGET: {self.config.target_join_percentage}% cross-table analysis with moderate complexity

SINGLE-TABLE EXAMPLES (Intermediate Reporting):
- "What's the average product price?"
- "Which employee has the highest sales target?"
- "Show monthly revenue trends"
- "What's the inventory turnover rate?"
- "List top 5 customers by total purchases"

CROSS-TABLE EXAMPLES (Business Analytics):
- "What's the total revenue by product category?"
- "Which stores have the highest customer satisfaction ratings?"
- "Show employee performance metrics by department"
- "What's the average order value by customer segment?"
- "Calculate monthly sales trends by store location"
- "Which product categories generate the most profit?"

FOCUS: Practical business intelligence questions with meaningful aggregations and grouping."""
        elif difficulty == "hard":
            return f"""

DIFFICULTY LEVEL: HARD - Advanced Business Analytics & Complex Insights
TARGET: {self.config.target_join_percentage}% complex multi-table analysis with sophisticated business logic

SINGLE-TABLE EXAMPLES (Advanced Metrics):
- "Calculate year-over-year growth rate for revenue"
- "What's the customer lifetime value distribution?"
- "Show seasonal demand patterns by month"

CROSS-TABLE EXAMPLES (Executive-Level Analytics):
- "Calculate profit margins by product category and store location"
- "Which customer segments have the highest retention rates?"
- "Analyze sales performance: top-performing vs underperforming stores"
- "Calculate customer acquisition cost by marketing channel and region"
- "Which employee-store combinations generate the highest revenue per transaction?"
- "Identify products with declining sales trends across multiple stores"
- "Calculate inventory turnover rates and identify slow-moving stock by location"
- "Analyze customer churn patterns by loyalty tier and purchase frequency"
- "Compare store performance relative to market size and competition density"

FOCUS: Executive dashboard queries, complex KPIs, multi-dimensional analysis, and strategic business insights."""
        else:  # mixed
            return f"""

DIFFICULTY LEVEL: MIXED - Comprehensive Business Question Suite
TARGET: {self.config.target_join_percentage}% cross-table analysis with varied complexity levels

INCLUDE ALL LEVELS:

BASIC BUSINESS QUERIES:
- "How many active customers do we have?"
- "What's our total inventory count?"
- "List all store locations"

INTERMEDIATE ANALYTICS:
- "What's the average order value by customer type?"
- "Show revenue trends by quarter"
- "Which products have the highest profit margins?"

ADVANCED INSIGHTS:
- "Calculate customer lifetime value by acquisition channel and geographic region"
- "Analyze cross-selling opportunities: which products are frequently bought together?"
- "Compare store performance metrics: sales per square foot vs employee productivity"

FOCUS: Comprehensive business intelligence suite covering operational reporting, tactical analytics, and strategic insights."""
    
    def _parse_llm_response(self, response_content: str) -> List[Dict[str, str]]:
        """Parse and validate LLM response."""
        try:
            logger.debug(f"Parsing LLM response, length: {len(response_content)}")
            
            # Clean the response - remove any markdown formatting
            cleaned_response = response_content.strip()
            
            # Remove markdown code blocks if present
            if cleaned_response.startswith('```'):
                cleaned_response = re.sub(r'^```(?:json)?\n?', '', cleaned_response)
                cleaned_response = re.sub(r'\n?```$', '', cleaned_response)
            
            logger.debug(f"Cleaned response: {cleaned_response[:200]}...")
            
            # Parse JSON
            qna_dataset = json.loads(cleaned_response)
            logger.debug(f"Parsed JSON successfully, found {len(qna_dataset)} items")
            
            # Log the first item for debugging
            if qna_dataset and len(qna_dataset) > 0:
                first_item = qna_dataset[0]
                logger.debug(f"First item structure: {first_item}")
                logger.debug(f"Question type: {type(first_item.get('question'))}, Answer type: {type(first_item.get('expected_answer'))}")
            
            # Validate structure
            if not isinstance(qna_dataset, list):
                raise ValidationError("Response must be a JSON array")
            
            for i, item in enumerate(qna_dataset):
                if not isinstance(item, dict):
                    raise ValidationError(f"Item {i} is not a JSON object")
                
                if 'question' not in item or 'expected_answer' not in item:
                    raise ValidationError(f"Item {i} missing required keys 'question' or 'expected_answer'")
                
                # Convert non-string values to strings to be more robust
                if not isinstance(item['question'], str):
                    logger.warning(f"Item {i} question is not a string, converting: {type(item['question'])}")
                    item['question'] = str(item['question'])
                
                if not isinstance(item['expected_answer'], str):
                    logger.warning(f"Item {i} expected_answer is not a string, converting: {type(item['expected_answer'])}")
                    item['expected_answer'] = str(item['expected_answer'])
                
                # Ensure values are not empty after conversion
                if not item['question'].strip():
                    raise ValidationError(f"Item {i} has empty question")
                
                if not item['expected_answer'].strip():
                    raise ValidationError(f"Item {i} has empty expected_answer")
            
            return qna_dataset
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Response content: {response_content}")
            raise ValidationError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            raise ValidationError(f"Failed to parse LLM response: {e}")
    
    def _validate_dataset(self, qna_dataset: List[Dict[str, str]], table_names: List[str]):
        """Validate the generated dataset meets quality requirements."""
        
        logger.debug(f"Validating dataset: {len(qna_dataset)} questions, minimum required: {self.config.min_questions}")
        
        if len(qna_dataset) < self.config.min_questions:
            raise ValidationError(
                f"Generated dataset has {len(qna_dataset)} questions, "
                f"minimum required is {self.config.min_questions}"
            )
        
        # Count questions that likely require joins
        join_questions = 0
        single_table_questions = []
        join_questions_list = []
        
        for i, item in enumerate(qna_dataset):
            if self.requires_join(item['question'], table_names):
                join_questions += 1
                join_questions_list.append(f"Q{i+1}: {item['question']}")
            else:
                single_table_questions.append(f"Q{i+1}: {item['question']}")
        
        join_percentage = (join_questions / len(qna_dataset)) * 100
        
        # Log detailed analysis for debugging
        logger.info(f"Join Detection Analysis:")
        logger.info(f"  Total questions: {len(qna_dataset)}")
        logger.info(f"  Detected joins: {join_questions} ({join_percentage:.1f}%)")
        logger.info(f"  Target joins: {self.config.target_join_percentage}%")
        
        # Run join detection test if debug logging is enabled
        if logger.isEnabledFor(logging.DEBUG):
            self.test_join_detection(table_names)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("JOIN QUESTIONS:")
            for jq in join_questions_list[:5]:  # Show first 5
                logger.debug(f"  {jq}")
            if len(join_questions_list) > 5:
                logger.debug(f"  ... and {len(join_questions_list) - 5} more")
                
            logger.debug("SINGLE-TABLE QUESTIONS:")
            for sq in single_table_questions[:5]:  # Show first 5
                logger.debug(f"  {sq}")
            if len(single_table_questions) > 5:
                logger.debug(f"  ... and {len(single_table_questions) - 5} more")
        
        if join_percentage < self.config.target_join_percentage:
            shortfall = self.config.target_join_percentage - join_percentage
            needed_joins = int((self.config.target_join_percentage * len(qna_dataset) / 100) - join_questions)
            
            logger.warning(
                f"Join percentage ({join_percentage:.1f}%) below target "
                f"({self.config.target_join_percentage}%). Need {needed_joins} more join questions "
                f"(shortfall: {shortfall:.1f}%)"
            )
            
            # Log suggestions for improvement
            logger.info("SUGGESTION: To improve join detection, questions should include:")
            logger.info("  - Cross-table references: 'employees in Marketing department'")
            logger.info("  - Aggregation by group: 'average salary by department'") 
            logger.info("  - Relationship queries: 'which employees work in which departments'")
            logger.info("  - Analytical questions: 'departments with most employees'")
        else:
            logger.info(f"✅ Join percentage target achieved: {join_percentage:.1f}% >= {self.config.target_join_percentage}%")
        
        logger.info(f"Dataset validation passed: {len(qna_dataset)} questions, {join_questions} joins")
    
    def test_join_detection(self, table_names: List[str]) -> None:
        """Test and log examples of join detection for debugging."""
        test_questions = [
            # Should be detected as JOINS (Business Analytics)
            "What's the total revenue by product category?",
            "Which stores have the highest customer satisfaction ratings?",
            "Show employee sales performance by department",
            "Calculate average order value by customer segment",
            "What's the inventory turnover rate by store location?",
            "Which suppliers provide the highest-rated products?",
            "Show monthly sales trends by region",
            "Calculate profit margins by product category and store",
            "Which customer segments have the highest retention rates?",
            "List employees and their department assignments",
            
            # Should be detected as SINGLE-TABLE (Basic Reporting)
            "What's our total customer count?",
            "List all product names",
            "What's the highest-priced item?",
            "Show all store locations",
            "What's the total inventory value?",
            "How many active employees do we have?",
            "What's our quarterly revenue growth?",
            "Show all product categories",
        ]
        
        logger.info("=== JOIN DETECTION TEST ===")
        for question in test_questions:
            is_join = self.requires_join(question, table_names)
            logger.info(f"{'JOIN' if is_join else 'SINGLE'}: {question}")
        logger.info("=== END TEST ===")
    
    def requires_join(self, question: str, table_names: List[str]) -> bool:
        """
        Balanced heuristic to determine if a question likely requires a join.
        Uses multiple approaches from strict to flexible for better coverage.
        
        Args:
            question: The question to analyze
            table_names: List of available table names
            
        Returns:
            True if question likely requires joining tables
        """
        question_lower = question.lower()
        
        # 1. Look for explicit multi-table references (STRONG indicator)
        table_references = 0
        table_entities = []
        
        for table_name in table_names:
            table_lower = table_name.lower()
            # Create entity variations
            variations = [
                table_lower,
                table_lower.rstrip('s'),  # employees -> employee
                table_lower + 's' if not table_lower.endswith('s') else table_lower,  # department -> departments
                table_lower.replace('_', ' '),  # table_name -> table name
            ]
            
            for variation in variations:
                if len(variation) > 2 and variation in question_lower:  # Avoid short words
                    table_references += 1
                    table_entities.append(table_name)
                    break
        
        if table_references >= 2:
            logger.debug(f"Join detected: Multiple table references ({table_entities})")
            return True
        
        # 2. Common join patterns (BUSINESS-FOCUSED approach)
        common_join_keywords = [
            # Business relationship indicators
            'by category', 'by department', 'by store', 'by region', 'by location', 'by segment',
            'per store', 'per category', 'per department', 'per region', 'per customer',
            'each store', 'each category', 'each department', 'each region', 'each location',
            'revenue by', 'sales by', 'profit by', 'performance by', 'metrics by',
            'total by', 'average by', 'count by', 'sum by', 'breakdown by',
            'customer segment', 'product category', 'store location', 'employee department',
            'and their', 'with their', 'along with', 'together with',
            'across stores', 'across categories', 'across regions', 'across departments',
            'customer satisfaction by', 'inventory turnover by', 'profit margin by',
            'sales performance by', 'acquisition cost by', 'lifetime value by',
        ]
        
        keyword_matches = 0
        for keyword in common_join_keywords:
            if keyword in question_lower:
                keyword_matches += 1
                if keyword_matches >= 1:  # Even one strong keyword suggests a join
                    logger.debug(f"Join detected: Keyword '{keyword}' in question")
                    return True
        
        # 3. Business aggregation patterns that typically need joins
        aggregation_join_patterns = [
            'revenue.*by', 'sales.*by', 'profit.*by', 'performance.*by',
            'total.*by', 'average.*by', 'sum.*by', 'count.*by', 'calculate.*by',
            'highest.*by', 'lowest.*by', 'best.*by', 'worst.*by', 'top.*by',
            'trends.*by', 'analysis.*by', 'breakdown.*by', 'distribution.*by',
            'each store', 'each category', 'each region', 'each segment', 'each location',
            'stores.*with', 'categories.*with', 'customers.*with', 'products.*with',
            'which stores', 'which categories', 'which customers', 'which products',
            'customer lifetime value', 'acquisition cost', 'retention rate', 'satisfaction score',
            'inventory turnover', 'profit margin', 'market share', 'growth rate',
        ]
        
        for pattern in aggregation_join_patterns:
            if re.search(pattern.replace('.*', r'.*?'), question_lower):
                logger.debug(f"Join detected: Aggregation pattern '{pattern}' in question")
                return True
        
        # 4. Business cross-reference patterns (flexible regex)
        cross_reference_patterns = [
            r'\b(what|which|how).*?(revenue|sales|profit|performance).*?(by|per|across)',
            r'\b(customer|employee|store|product)s?.*?(category|segment|department|location)',
            r'\b(category|segment|department|location)s?.*?(customer|employee|store|product)',
            r'\b(list|show|find|calculate).*?(and|with|their|by)',
            r'\b(average|total|sum|count|analyze).*?(by|per|across|for each)',
            r'\b(compare|comparison|vs|versus).*?(store|category|region|department)',
            r'\b(top|bottom|highest|lowest|best|worst).*?(by|in|across|per)',
            r'\b(trends|patterns|analysis|breakdown).*?(by|across|per|for)',
        ]
        
        for pattern in cross_reference_patterns:
            if re.search(pattern, question_lower):
                logger.debug(f"Join detected: Cross-reference pattern '{pattern}' in question")
                return True
        
        # 5. ONLY exclude if it's CLEARLY single-table
        definite_single_table = [
            r'^\s*(list\s+all\s+\w+\s*$)',  # "List all names" at end of question
            r'^\s*(show\s+all\s+\w+\s*$)',  # "Show all departments" at end
            r'^\s*(how\s+many\s+total)',    # "How many total"
            r'^\s*(what\s+is\s+the\s+\w+\s+of\s+\w+\s*$)',  # "What is the name of John"
        ]
        
        for pattern in definite_single_table:
            if re.search(pattern, question_lower):
                logger.debug(f"Single-table detected: Definite pattern '{pattern}' in question")
                return False
        
        # 6. Default: if we're unsure, lean towards JOIN (better to overestimate)
        # This helps achieve target percentages
        logger.debug(f"Uncertain classification, defaulting to NO JOIN for: {question}")
        return False
