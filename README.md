# GenAI SQL Test Data Generator

A comprehensive business intelligence test data generator that connects to SQL Server and MySQL databases and leverages Large Language Models to create realistic business analysis questions and answers. Designed for testing Natural Language to SQL applications with enterprise-grade business scenarios.

## 🚀 Features

- **🗣️ Natural Language Questions**: Generates conversational business questions without technical database terminology
- **📊 Visualization-Focused**: 60% of questions are designed for charts, graphs, and dashboards
- **🏢 Business-Focused Analytics**: Realistic BI queries for sales analysis, customer analytics, inventory management, and performance metrics
- **� Four Difficulty Levels**: From basic reporting to advanced executive analytics with strategic insights
- **🔍 Automated Schema Discovery**: Intelligent database analysis with relationship detection
- **🤝 Relational Data Sampling**: Smart sampling across connected tables for consistent test data
- **🤖 AI-Powered Generation**: Uses GPT-4 to create diverse, contextually relevant business questions
- **📈 Join-Focused Testing**: Configurable cross-table analysis percentage (20%-70% based on difficulty)
- **🌐 REST API**: Complete FastAPI web service with async processing
- **📱 Web Interface**: User-friendly browser-based interface for non-technical users
- **📁 Multiple Output Formats**: JSON datasets, downloadable files, and API responses

## 🎯 Business Question Types Generated

### **📈 Sales Analysis** (Natural Language)
- "What's the total revenue for each store?"
- "Which products have sold the most units?"
- "What's the average transaction value per store?"
- "Show monthly sales trends for the current year"
- "Which payment methods are most popular?"

### **👥 Customer Analysis** (Conversational)
- "What's the average customer lifetime value by loyalty tier?"
- "Which customers haven't made a purchase in the last 6 months?"
- "Show customer distribution by state"
- "What's the average age of customers by loyalty tier?"
- "Which customers have written the most reviews?"

### **📦 Inventory & Operations** (Business Focused)
- "Which products are running low on stock (below reorder point)?"
- "What's the inventory value for each store?"
- "Which suppliers have the highest rated products?"
- "Show employee performance by transaction count"
- "What's the average review rating for each product category?"

### **💼 Advanced Analytics** (Executive Level)
- "Calculate profit margins for each product category by store"
- "Which store-product combinations generate the highest revenue?"
- "What's the seasonal revenue trend for each product category?"
- "Calculate customer acquisition cost vs lifetime value by region"
- "Segment customers by purchase frequency and average order value"
- "Which products are frequently bought together (market basket analysis)?"

### **📊 Visualization-Focused Questions** (60% Priority)
*Perfect for charts, graphs, and dashboards*

#### Time Series Visualizations:
- "Daily sales trends over the past year"
- "Monthly revenue breakdown by product category"
- "Quarterly revenue trends with year-over-year comparison"

#### Comparison Visualizations:
- "Top 10 best-selling products by revenue"
- "Store ranking by total transactions processed"
- "Revenue composition by payment method across stores"

#### Distribution Visualizations:
- "Distribution of customer lifetime values"
- "Customer distribution by loyalty tier"
- "Product price distribution across categories"

#### Geographic Visualizations:
- "Sales density by state/region"
- "Store locations with revenue bubble sizes"
- "Revenue per square mile by region"

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

| Level | Join % | Visualization Focus | Description | Example Questions |
|-------|--------|-------------------|-------------|-------------------|
| **Easy** | 20% | 60% | Basic business reporting with simple charts | "How many customers do we have?", "Customer distribution by loyalty tier" |
| **Medium** | 40% | 60% | Business analytics with meaningful visualizations | "Monthly revenue breakdown by product category", "Store ranking by customer satisfaction" |
| **Hard** | 70% | 60% | Advanced analytics with complex visualizations | "Customer churn rate visualization by loyalty tier", "Inventory turnover heatmap by product and store" |
| **Mixed** | 40% | 60% | Comprehensive suite spanning all complexity levels | Balanced mix from simple charts to executive dashboards |

### 📊 Natural Language Focus

All questions are generated using natural, conversational language that:
- **Avoids technical database terminology** (no table names, column references)
- **Sounds like real business conversations** analysts would have
- **Uses business metrics and KPIs** instead of technical terms
- **Perfect for testing Natural Language to SQL** systems

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

## 📋 Sample Natural Language Output

### Basic Analytics Questions
```json
[
  {
    "question": "What's the total revenue for each store?",
    "expected_answer": "Downtown Store: $2,450,000, Mall Location: $1,890,000, Airport Branch: $1,230,000"
  },
  {
    "question": "Which products have sold the most units?",
    "expected_answer": "Wireless Headphones (2,540 units), Smart Watch (1,890 units), Phone Case (1,650 units)"
  },
  {
    "question": "Show customer distribution by loyalty tier",
    "expected_answer": "Gold: 45%, Silver: 35%, Bronze: 20%"
  }
]
```

### Visualization-Ready Questions
```json
[
  {
    "question": "Daily sales trends over the past year",
    "expected_answer": "Peak sales in December ($450K), lowest in February ($280K), steady growth Q2-Q3"
  },
  {
    "question": "Top 10 best-selling products by revenue",
    "expected_answer": "Premium Laptop ($890K), Gaming Console ($670K), Wireless Speaker ($450K)..."
  },
  {
    "question": "Sales performance by day of week and hour of day",
    "expected_answer": "Peak: Saturday 2-4 PM ($45K/hr), Lowest: Monday 6-8 AM ($8K/hr)"
  }
]
```

### Advanced Business Intelligence
```json
[
  {
    "question": "Calculate profit margins for each product category by store",
    "expected_answer": "Electronics: Downtown 24%, Mall 18%; Clothing: Downtown 32%, Mall 28%"
  },
  {
    "question": "Which products are frequently bought together (market basket analysis)?",
    "expected_answer": "Phone + Case (78%), Laptop + Mouse (65%), Gaming Console + Controller (89%)"
  },
  {
    "question": "Customer churn rate by loyalty tier and registration cohort",
    "expected_answer": "Gold Tier 2024: 5%, Silver Tier 2024: 12%, Bronze Tier 2024: 25%"
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
- **`src/database_connector.py`**: SQL Server/MySQL connectivity and schema discovery
- **`src/llm_generator.py`**: Enhanced LangChain/OpenAI integration with natural language focus and visualization optimization
- **`src/exceptions.py`**: Custom exception classes
- **`api/main.py`**: FastAPI REST service with async processing

## Workflow

1. **Database Connection**: Connects to SQL Server or MySQL using provided credentials
2. **Schema Discovery**: Analyzes table structures and foreign key relationships
3. **Relational Sampling**: Fetches consistent sample data across related tables
4. **Context Building**: Constructs comprehensive business context for the LLM
5. **Natural Language Q&A Generation**: Uses GPT-4 to generate conversational business questions with 60% visualization focus
6. **Quality Validation**: Ensures natural language style, visualization readiness, and join percentage targets
7. **Output**: Saves structured JSON dataset optimized for Natural Language to SQL testing

## 🎯 Business Intelligence Capabilities

### Question Categories Generated
- **📊 Operational Analytics**: Daily operations, inventory, basic reporting (natural language style)
- **💼 Management Insights**: Performance metrics, departmental analysis, trends (visualization-ready)
- **🏆 Executive Intelligence**: Strategic analysis, profitability, market insights (dashboard-perfect)
- **🔄 Cross-Functional**: Multi-department analysis requiring complex joins (chart-optimized)
- **📈 Visualization-Focused**: 60% of all questions designed for specific chart types (line, bar, pie, heatmap, geographic)

### Performance Metrics
- **Generation Speed**: < 90 seconds for comprehensive datasets
- **Question Quality**: 15+ natural language Q&A pairs per table
- **Visualization Focus**: 60% of questions optimized for charts and dashboards
- **Join Coverage**: 20%-70% based on difficulty level
- **Natural Language**: 100% conversational, business-focused questions
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

## 🧪 Testing & Development

### Test Structure

The project has a comprehensive test suite organized into three categories:

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_wrapper.py      # Database connector wrapper tests
│   ├── test_schema_fix.py   # Schema qualification tests
│   └── ...
├── integration/             # Integration tests for full workflows
│   ├── test_api_*.py        # API endpoint tests
│   ├── test_*connection*.py # Database connection tests
│   ├── test_*discovery*.py  # Database discovery tests
│   └── test_mysql*.py       # MySQL-specific tests
└── debug/                   # Debug utilities and diagnostic tools
    ├── check_tables.py      # Database table verification
    ├── debug_schema.py      # Schema investigation tools
    └── ...
```

### Running Tests

Use the built-in test runner:

```bash
# Run all tests
python run_tests.py

# Run specific test suites
python run_tests.py unit           # Unit tests only
python run_tests.py integration    # Integration tests only  
python run_tests.py debug          # Debug utilities only

# Run specific test file
python run_tests.py -f test_wrapper          # Finds in any test directory
python run_tests.py -f check_tables         # Run debug utility
```

### Manual Test Execution

You can also run tests directly:

```bash
# Run a specific test
python tests/unit/test_wrapper.py

# Run debug utilities
python tests/debug/check_tables.py
```

### Development Environment

```bash
# Install development dependencies (if using pytest)
pip install pytest pytest-cov

# Code formatting
black .

# Linting
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
