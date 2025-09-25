# 🚀 GenAI SQL Test Data Generator - FastAPI Web Service

A REST API service that provides database discovery and Q&A dataset generation capabilities through HTTP endpoints.

## 🌟 **API Features**

- 🔍 **Database Discovery**: Automatically discover database tables, schemas, and relationships
- 🤖 **Q&A Generation**: Generate test datasets using LLM with emphasis on join queries  
- 📊 **Interactive Analysis**: Get recommendations and optimal table suggestions
- ⚡ **Async Processing**: Background jobs for long-running operations
- 📁 **File Downloads**: Export generated datasets as JSON files
- 📖 **Auto Documentation**: Interactive API docs with Swagger UI

## 🚀 **Quick Start**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
# Development server with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or use the startup script
python start_api.py
```

### 3. Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 **API Endpoints**

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service information |
| `GET` | `/health` | Health check |
| `POST` | `/discover` | Database discovery |
| `POST` | `/generate` | Q&A generation (sync) |
| `POST` | `/generate-async` | Q&A generation (async) |
| `GET` | `/jobs/{job_id}` | Job status |
| `GET` | `/download/{job_id}` | Download dataset |

### Interactive Documentation
Visit http://localhost:8000/docs for interactive API documentation with:
- 📝 Request/response schemas
- 🧪 Try-it-out functionality  
- 📋 Example requests
- 🔍 Parameter descriptions

## 🧪 **API Usage Examples**

### 1. Database Discovery

**Request (SQL Server):**
```bash
curl -X POST "http://localhost:8000/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "database_config": {
      "server": "your-server.database.windows.net",
      "database": "your_database",
      "username": "your_username", 
      "password": "your_password",
      "db_type": "sqlserver",
      "port": 1433
    },
    "exclude_tables": ["sys", "temp"],
    "max_tables": 10
  }'
```

**Request (MySQL):**
```bash
curl -X POST "http://localhost:8000/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "database_config": {
      "server": "localhost",
      "database": "testdb",
      "username": "testuser", 
      "password": "testpass",
      "db_type": "mysql",
      "port": 3306
    },
    "exclude_tables": ["information_schema", "performance_schema"],
    "max_tables": 10
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully analyzed 8 tables",
  "tables": [
    {
      "name": "Employees",
      "column_count": 6,
      "columns": [
        {"column_name": "EmployeeID", "data_type": "int", "is_nullable": false},
        {"column_name": "FirstName", "data_type": "varchar", "is_nullable": false}
      ]
    }
  ],
  "relationships": [
    {
      "fk_name": "FK_Employees_Departments",
      "parent_table": "Employees",
      "parent_column": "DepartmentID",
      "referenced_table": "Departments", 
      "referenced_column": "DepartmentID"
    }
  ],
  "recommendations": [
    "Good join potential (75%). Should generate quality relational questions."
  ],
  "suggested_tables": ["Employees", "Departments", "Projects"],
  "join_potential": 75.0
}
```

### 2. Q&A Dataset Generation

**Request (SQL Server):**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "database_config": {
      "server": "your-server.database.windows.net",
      "database": "your_database", 
      "username": "your_username",
      "password": "your_password",
      "db_type": "sqlserver"
    },
    "openai_config": {
      "api_key": "sk-your-openai-api-key",
      "model": "gpt-4"
    },
    "generation_config": {
      "sample_size": 10,
      "min_questions": 15,
      "target_join_percentage": 40
    },
    "tables": ["Employees", "Departments"],
    "discover_all": false
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully generated 15 Q&A pairs",
  "dataset": [
    {
      "question": "How many employees work in the Engineering department?",
      "expected_answer": "5"
    },
    {
      "question": "What is the average salary of all employees?",
      "expected_answer": "75000"
    }
  ],
  "metadata": {
    "tables_analyzed": ["Employees", "Departments"],
    "table_count": 2,
    "relationship_count": 1,
    "generation_timestamp": "2025-09-24T10:30:00Z"
  },
  "statistics": {
    "total_questions": 15,
    "join_questions": 6,
    "join_percentage": 40.0,
    "meets_target": true
  }
}
```

### 3. Discover Whole Database (Auto-Mode)

**Request:**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "database_config": {
      "server": "your-server.database.windows.net",
      "database": "your_database",
      "username": "your_username",
      "password": "your_password",
      "db_type": "sqlserver"
    },
    "openai_config": {
      "api_key": "sk-your-openai-api-key"
    },
    "discover_all": true,
    "exclude_tables": ["sys", "log", "temp"]
  }'
```

### 4. Asynchronous Generation

**Start Job:**
```bash
curl -X POST "http://localhost:8000/generate-async" \
  -H "Content-Type: application/json" \
  -d '{ ... same request as generate ... }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0.0,
  "created_at": "2025-09-24T10:30:00Z"
}
```

**Check Status:**
```bash
curl "http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000"
```

**Download Results:**
```bash
curl "http://localhost:8000/download/550e8400-e29b-41d4-a716-446655440000" \
  -o dataset.json
```

## 🐍 **Python Client Example**

```python
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

# Database configuration (SQL Server example)
db_config = {
    "server": "your-server.database.windows.net",
    "database": "your_database",
    "username": "your_username", 
    "password": "your_password",
    "db_type": "sqlserver",
    "port": 1433
}

# For MySQL, use:
# db_config = {
#     "server": "localhost",
#     "database": "testdb",
#     "username": "testuser", 
#     "password": "testpass",
#     "db_type": "mysql",
#     "port": 3306
# }

openai_config = {
    "api_key": "sk-your-openai-api-key",
    "model": "gpt-4"
}

# 1. Discover database
discovery_request = {
    "database_config": db_config,
    "exclude_tables": ["sys", "temp"],
    "max_tables": 8
}

response = requests.post(f"{BASE_URL}/discover", json=discovery_request)
discovery_result = response.json()

print(f"Found {len(discovery_result['tables'])} tables")
print(f"Join potential: {discovery_result['join_potential']:.1f}%")

# 2. Generate Q&A dataset
generation_request = {
    "database_config": db_config,
    "openai_config": openai_config,
    "generation_config": {
        "sample_size": 15,
        "min_questions": 20,
        "target_join_percentage": 40
    },
    "tables": discovery_result['suggested_tables'][:5]  # Use top 5 suggested tables
}

response = requests.post(f"{BASE_URL}/generate", json=generation_request)
generation_result = response.json()

if generation_result['success']:
    dataset = generation_result['dataset']
    print(f"Generated {len(dataset)} Q&A pairs")
    
    # Save to file
    with open('qna_dataset.json', 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print("Dataset saved to qna_dataset.json")
else:
    print(f"Generation failed: {generation_result['message']}")
```

## �️ **Database Support**

### Supported Database Types

The API supports both **SQL Server** and **MySQL** databases:

| Database | db_type Value | Default Port | Required Fields |
|----------|---------------|--------------|-----------------|
| SQL Server | `sqlserver` or `mssql` | 1433 | server, database, username, password |
| MySQL | `mysql` | 3306 | server, database, username, password |

### Database Configuration Examples

**SQL Server:**
```json
{
  "database_config": {
    "server": "server.database.windows.net",
    "database": "CompanyDB",
    "username": "dbuser",
    "password": "securepass",
    "db_type": "sqlserver",
    "port": 1433,
    "driver": "ODBC Driver 17 for SQL Server"
  }
}
```

**MySQL:**
```json
{
  "database_config": {
    "server": "mysql-host.com",
    "database": "business_db",
    "username": "mysql_user",
    "password": "mysql_pass",
    "db_type": "mysql", 
    "port": 3306,
    "driver": "mysql+pymysql"
  }
}
```

**Local MySQL (Docker):**
```json
{
  "database_config": {
    "server": "localhost",
    "database": "testdb",
    "username": "testuser",
    "password": "testpass",
    "db_type": "mysql",
    "port": 3306
  }
}
```

### Database Requirements

Both database types require:
- **Foreign Key Relationships**: Essential for generating join-based questions
- **Business-Relevant Tables**: Customer, sales, product, employee, or similar business entities
- **Sample Data**: At least 10-50 rows per table for meaningful question generation

### Quick Test with Docker MySQL

```bash
# Start MySQL with sample data
docker-compose up mysql

# Test connection
curl -X POST "http://localhost:8000/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "database_config": {
      "server": "localhost",
      "database": "testdb", 
      "username": "testuser",
      "password": "testpass",
      "db_type": "mysql"
    }
  }'
```

## �🔧 **Configuration**

### Environment Variables
The API uses a unified configuration approach with prefixed environment variables:

```env
# Database Type Selection
DB_TYPE=mysql  # Options: sqlserver, mssql, mysql

# MySQL Database Configuration
MYSQL_DB_SERVER=localhost
MYSQL_DB_DATABASE=testdb
MYSQL_DB_USERNAME=testuser
MYSQL_DB_PASSWORD=testpass
MYSQL_DB_PORT=3306

# SQL Server Database Configuration
SQLSERVER_DB_SERVER=your-server.database.windows.net
SQLSERVER_DB_DATABASE=your_database
SQLSERVER_DB_USERNAME=your_username
SQLSERVER_DB_PASSWORD=your_password
SQLSERVER_DB_PORT=1433

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Logging
LOG_LEVEL=INFO
```

**Configuration Benefits:**
- ✅ **Single `.env` file** for both database types
- ✅ **Quick database switching** by changing `DB_TYPE`
- ✅ **No credential conflicts** with prefixed variables
- ✅ **Backward compatibility** with existing `DB_*` variables

### Production Settings
For production deployment:

```python
# In api/main.py, update CORS settings:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 🚀 **Deployment Options**

### 1. Docker Deployment
```bash
# Build image
docker build -t qna-generator-api .

# Run container
docker run -p 8000:8000 qna-generator-api
```

### 2. Cloud Deployment (Azure, AWS, GCP)
```bash
# Using gunicorn for production
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 3. Local Development
```bash
# Auto-reload development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 **Monitoring & Observability**

- **Health Endpoint**: `/health` for monitoring
- **Structured Logging**: JSON logs for production
- **Metrics**: Request/response times and success rates
- **Error Tracking**: Detailed error responses with correlation IDs

## 🔒 **Security Considerations**

- 🔐 **API Keys**: Never expose OpenAI API keys in client-side code
- 🛡️ **Database Access**: Use read-only database credentials
- 🌐 **CORS**: Configure appropriate origins for production
- 🔍 **Input Validation**: All inputs validated with Pydantic models
- 📝 **Logging**: Sensitive data excluded from logs

## 🎯 **API Benefits**

✅ **Easy Integration**: REST API works with any programming language  
✅ **Scalable**: Async processing for large datasets  
✅ **Interactive**: Built-in documentation and testing  
✅ **Flexible**: Support for both specific tables and whole database analysis  
✅ **Production Ready**: Error handling, logging, and monitoring  

Start the API and visit http://localhost:8000/docs to explore all endpoints! 🚀
