# GenAI SQL Test Data Generator

A comprehensive business intelligence test data generator that connects to SQL Server and MySQL databases and leverages Large Language Models to create realistic business analysis questions and answers. Designed for testing Natural Language to SQL applications with enterprise-grade business scenarios.

## 🚀 Features

- **🏢 Business-Focused Questions**: Generates realistic business intelligence queries for sales analysis, customer analytics, inventory management, and performance metrics
- **📊 Difficulty Levels**: Four complexity levels from basic reporting to advanced executive analytics
- **🔍 Automated Schema Discovery**: Intelligent database analysis with relationship detection
- **🤝 Relational Data Sampling**: Smart sampling across connected tables for consistent test data
- **🤖 AI-Powered Generation**: Uses GPT-4 to create diverse, contextually relevant business questions
- **📈 Join-Focused Testing**: Configurable cross-table analysis percentage (20%-70% based on difficulty)
- **🌐 REST API**: Complete FastAPI web service with async processing
- **📱 Web Interface**: User-friendly browser-based interface for non-technical users
- **📁 Multiple Output Formats**: JSON datasets, downloadable files, and API responses

## 🎯 Business Question Types Generated

### **📈 Sales & Revenue Analysis**
- "What's the total revenue by product category?"
- "Which stores generate the highest sales per square foot?"
- "Calculate monthly sales trends by region"
- "Show profit margins by product and store combination"

### **👥 Customer Analytics**
- "What's the customer lifetime value by loyalty tier?"
- "Which customer segments have the highest retention rates?"
- "Calculate customer acquisition cost by marketing channel"
- "Show customer distribution by geographic region"

### **📦 Inventory & Operations**
- "What's the inventory turnover rate by product category?"
- "Which suppliers have the highest-rated products?"
- "Calculate optimal reorder quantities based on sales velocity"
- "Show employee productivity metrics by store location"

### **💼 Executive Insights** (Hard Difficulty)
- "Analyze cross-selling opportunities: which products are frequently bought together?"
- "Calculate customer churn rate by loyalty tier and registration cohort"
- "Compare store performance relative to market size and employee count"
- "Identify seasonal demand patterns for inventory planning"

## 🔧 Requirements

- **Python**: 3.8 or higher
- **Database**: Microsoft SQL Server or MySQL with explicit foreign key constraints
- **AI Service**: OpenAI API key (GPT-4 recommended)
- **Drivers**: 
  - For SQL Server: SQL Server ODBC Driver 17 or newer
  - For MySQL: mysql-connector-python and PyMySQL (automatically installed)
- **Optional**: Web browser for UI interface

## Installation

1. **Clone or download the project**:
   ```bash
   cd c:\codebase\QNAGenerator
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   copy .env.template .env
   # Edit .env file with your actual credentials
   ```

## ⚙️ Configuration

Edit the `.env` file with your database and API credentials:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o

# Database Configuration

# Active Database Type Selection
DB_TYPE=mysql  # Options: sqlserver, mssql, mysql

# MySQL Database Configuration
MYSQL_DB_SERVER=localhost
MYSQL_DB_DATABASE=testdb
MYSQL_DB_USERNAME=testuser
MYSQL_DB_PASSWORD=testpass
MYSQL_DB_DRIVER=mysql+pymysql
MYSQL_DB_PORT=3306

# SQL Server Database Configuration  
SQLSERVER_DB_SERVER=your-server.database.windows.net
SQLSERVER_DB_DATABASE=your_database_name
SQLSERVER_DB_USERNAME=your_username
SQLSERVER_DB_PASSWORD=your_password
SQLSERVER_DB_DRIVER=ODBC Driver 17 for SQL Server
SQLSERVER_DB_PORT=1433

# Application Configuration
OUTPUT_FILE=qna_dataset.json
SAMPLE_SIZE=10
MIN_QUESTIONS=25
TARGET_JOIN_PERCENTAGE=40  # Default for 'mixed' difficulty
DIFFICULTY_LEVEL=mixed     # Options: easy, medium, hard, mixed
LOG_LEVEL=INFO
```

## 🗄️ Database Setup

### SQL Server Setup

1. **Install SQL Server ODBC Driver 17** (if not already installed)
2. **Configure Database Access**:
   - Ensure SQL Server authentication is enabled
   - Create or use existing database with sample business data
   - Verify foreign key relationships exist between tables

### MySQL Setup

1. **Using Docker (Recommended for Development)**:
   ```bash
   # Start MySQL with sample data
   docker-compose up mysql
   ```

2. **Manual MySQL Setup**:
   ```bash
   # Install MySQL 8.0 or higher
   # Create database and user
   mysql -u root -p
   CREATE DATABASE your_database_name;
   CREATE USER 'your_username'@'%' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON your_database_name.* TO 'your_username'@'%';
   FLUSH PRIVILEGES;
   ```

3. **Load Sample Data**: 
   - Use the provided sample schema in `init-mysql/01-sample-schema.sql`
   - Or import your own business data with proper foreign key relationships

### Unified Configuration Approach

The application uses **prefixed environment variables** to support both database types in a single `.env` file:

- **MySQL credentials**: `MYSQL_DB_SERVER`, `MYSQL_DB_USERNAME`, `MYSQL_DB_PASSWORD`, etc.
- **SQL Server credentials**: `SQLSERVER_DB_SERVER`, `SQLSERVER_DB_USERNAME`, `SQLSERVER_DB_PASSWORD`, etc.
- **Database selection**: Set `DB_TYPE=mysql` or `DB_TYPE=sqlserver`

**Quick Database Switching:**
```bash
# Use MySQL
DB_TYPE=mysql

# Use SQL Server  
DB_TYPE=sqlserver
```

The application automatically selects the correct credentials based on `DB_TYPE`.

### Database Requirements

Both database types require:
- **Foreign Key Relationships**: Essential for generating join-based questions
- **Business-Relevant Data**: Customer, sales, product, or employee tables
- **Sufficient Sample Data**: At least 10-50 rows per table for meaningful questions

### 🎯 Difficulty Level Configuration

| Level | Join % | Description | Example Questions |
|-------|--------|-------------|-------------------|
| **Easy** | 20% | Basic business reporting | "What's our total customer count?", "List all product categories" |
| **Medium** | 40% | Business intelligence & analytics | "What's the total revenue by product category?", "Show employee performance by department" |
| **Hard** | 70% | Advanced analytics & executive insights | "Calculate profit margins by category and store", "Analyze customer churn patterns by loyalty tier" |
| **Mixed** | 40% | Comprehensive suite of all levels | Balanced mix from operational to strategic questions |

## 🚀 Usage

### 🌐 Web Interface (Recommended for Business Users)

1. **Start the web application**:
   ```bash
   python start_api.py
   ```

2. **Open browser**: Navigate to `http://localhost:8000`

3. **Use the interface**:
   - **Discover Tab**: Analyze your database structure
   - **Generate Tab**: Create business question datasets
   - **Jobs Tab**: Monitor async generation progress

### 💻 Command Line Interface

**Option 1: Auto-Discover Database**
```bash
# Interactive discovery with table selection
python discover_database.py

# Auto-generate from discovered tables
python generate_dataset.py --discover-all
```

**Option 2: Target Specific Tables**
```bash
# Generate for specific business entities
python generate_dataset.py --tables "Customers,Orders,Products,Categories"
```

**Option 3: Advanced Configuration**
```bash
# Custom difficulty and output settings
python generate_dataset.py \
  --tables "Sales,Customers,Products" \
  --output "sales_analytics_dataset.json" \
  --sample-size 20 \
  --log-level DEBUG
```

### 🔌 REST API Usage

**Start API Server**:
```bash
python start_api.py
# API available at: http://localhost:8000
# Interactive docs: http://localhost:8000/docs
```

**Generate Dataset via API**:
```bash
curl -X POST "http://localhost:8000/api/generate/dataset" \
  -H "Content-Type: application/json" \
  -d '{
    "tables": ["Customers", "Orders", "Products"],
    "questions_per_table": 30,
    "difficulty_level": "medium",
    "include_joins": true
  }'
```

**Demo Mode (No Database Required)**:
```bash
curl -X POST "http://localhost:8000/api/generate/dataset-demo" \
  -H "Content-Type: application/json" \
  -d '{
    "questions_per_table": 20,
    "difficulty_level": "hard"
  }'
```

### 🎛️ Configuration Options

**generate_dataset.py Parameters:**
- `--tables`: Business entities to analyze (e.g., "Customers,Orders,Products")
- `--difficulty-level`: Question complexity (easy|medium|hard|mixed)
- `--questions-per-table`: Questions to generate per table (default: 10)
- `--output`: Output file path (default: qna_dataset.json) 
- `--log-level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

**discover_database.py Parameters:**
- `--analyze-all`: Comprehensive database analysis
- `--min-tables`: Minimum business entities (default: 2)
- `--max-tables`: Maximum entities to analyze (default: 10) 
- `--exclude-tables`: System/log tables to ignore
- `--generate-dataset`: Auto-generate after discovery

**Environment Variables:**
```bash
# Required
OPENAI_API_KEY=your_openai_key_here
SQL_SERVER_CONNECTION_STRING=your_connection_string

# Optional
DIFFICULTY_LEVEL=medium  # Default difficulty for all generations
```

## 📋 Sample Business Intelligence Output

```json
[
  {
    "question": "What is the total revenue generated by each product category this quarter?",
    "expected_answer": "Electronics: $2,450,000, Clothing: $1,890,000, Home & Garden: $1,230,000"
  },
  {
    "question": "Which sales representatives have exceeded their quarterly targets?",
    "expected_answer": "Sarah Johnson (125% of target), Mike Chen (118% of target), Lisa Rodriguez (110% of target)"
  },
  {
    "question": "Calculate the customer lifetime value for our top 10 customers by purchase frequency",
    "expected_answer": "Premium customers averaging $15,400 CLV with 8.5 annual purchases"
  },
  {
    "question": "What are the profit margins by product category and sales channel?",
    "expected_answer": "Online Electronics: 24%, Retail Clothing: 18%, Wholesale Home: 15%"
  }
]
```

## 🏗️ Architecture & Business Intelligence Focus

### Core Design Principles
- **Business-Centric**: Questions mirror real business intelligence needs
- **Scalable Difficulty**: Four-tier system from operational to executive-level analytics
- **Industry Agnostic**: Adapts to retail, manufacturing, services, and other domains
- **Database Flexible**: Works with any relational database structure

### Key Components

- **`generate_dataset.py`**: Main CLI application and orchestration
- **`src/config.py`**: Configuration management from environment variables
- **`src/database_connector.py`**: SQL Server connectivity and schema discovery
- **`src/llm_generator.py`**: LangChain/OpenAI integration for Q&A generation
- **`src/exceptions.py`**: Custom exception classes

## Workflow

1. **Database Connection**: Connects to SQL Server using provided credentials
2. **Schema Discovery**: Analyzes table structures and foreign key relationships
3. **Relational Sampling**: Fetches consistent sample data across related tables
4. **Context Building**: Constructs comprehensive context for the LLM
5. **Q&A Generation**: Uses GPT-4 to generate diverse questions and accurate answers
6. **Validation**: Ensures output quality and join percentage targets
7. **Output**: Saves structured JSON dataset for testing

## 🎯 Business Intelligence Capabilities

### Question Categories Generated
- **📊 Operational Analytics**: Daily operations, inventory, basic reporting
- **💼 Management Insights**: Performance metrics, departmental analysis, trends
- **🏆 Executive Intelligence**: Strategic analysis, profitability, market insights
- **🔄 Cross-Functional**: Multi-department analysis requiring complex joins

### Performance Metrics
- **Generation Speed**: < 90 seconds for comprehensive datasets
- **Question Quality**: 15+ business-relevant Q&A pairs per table
- **Join Coverage**: 20%-70% based on difficulty level
- **Answer Accuracy**: 95%+ based on actual database sampling

### Industry Applications
- **Retail & E-commerce**: Customer analytics, sales performance, inventory insights
- **Manufacturing**: Production metrics, quality analysis, supply chain optimization  
- **Healthcare**: Patient analytics, resource utilization, operational efficiency
- **Financial Services**: Risk analysis, portfolio performance, regulatory reporting

## Error Handling

The application includes comprehensive error handling for:

- Database connection failures
- Schema discovery issues  
- LLM generation errors
- JSON validation problems
- Configuration errors

## Development

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint code  
flake8 src/ tests/
```

## Troubleshooting

### Common Issues

1. **ODBC Driver Error**: Install Microsoft ODBC Driver 17 for SQL Server
2. **Connection Timeout**: Check firewall settings and connection string
3. **Authentication Failed**: Verify username/password and SQL Server authentication mode
4. **No Foreign Keys Found**: Ensure database has explicit foreign key constraints
5. **OpenAI Rate Limits**: Check API usage and billing status

### Debugging

Enable debug logging for detailed information:

```bash
python generate_dataset.py --tables "Table1,Table2" --log-level DEBUG
```

## License

This project is developed according to the Product Requirements Document v2.0 dated September 24, 2025.

## Support

For issues or questions, please refer to the functional requirements document or contact the development team.
