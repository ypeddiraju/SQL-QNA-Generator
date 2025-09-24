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

**Request:**
```bash
curl -X POST "http://localhost:8000/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "database_config": {
      "server": "your-server.database.windows.net",
      "database": "your_database",
      "username": "your_username", 
      "password": "your_password"
    },
    "exclude_tables": ["sys", "temp"],
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

**Request:**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "database_config": {
      "server": "your-server.database.windows.net",
      "database": "your_database", 
      "username": "your_username",
      "password": "your_password"
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
      "password": "your_password"
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

# Database configuration
db_config = {
    "server": "your-server.database.windows.net",
    "database": "your_database",
    "username": "your_username", 
    "password": "your_password"
}

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

## 🔧 **Configuration**

### Environment Variables
The API can use environment variables for default configurations:

```env
# Default database config (optional)
DEFAULT_DB_SERVER=your-server.database.windows.net
DEFAULT_DB_DATABASE=your_database

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Logging
LOG_LEVEL=INFO
```

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
