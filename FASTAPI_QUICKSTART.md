# 🚀 FastAPI Quick Start Guide

## **What You Now Have: Complete Web API + CLI**

You now have **both** a command-line interface AND a REST API web service!

### 🎯 **Two Ways to Use the Application**

| Method | Use Case | How to Start |
|--------|----------|--------------|
| **CLI** | Direct command-line usage | `python generate_dataset.py --discover-all` |
| **API** | Web applications, integrations | `python start_api.py` |

## 🚀 **Start the FastAPI Web Service**

### Option 1: Quick Start (Recommended)
```bash
# Start the API server
python start_api.py
```

### Option 2: Windows Batch Script
```bash
# Run the startup script
start_api.bat
```

### Option 3: Direct uvicorn
```bash
# Manual start with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 **Access the API**

Once started, you can access:

- **🔍 Interactive API Docs**: http://localhost:8000/docs
- **📚 Alternative Docs**: http://localhost:8000/redoc  
- **❤️ Health Check**: http://localhost:8000/health
- **📊 Service Info**: http://localhost:8000/

## 🧪 **Test the API**

### 1. Using the Interactive Docs (Easiest)
1. Go to http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in your database credentials
4. Execute the request

### 2. Using the Python Test Client
```bash
# Edit test_api_client.py with your credentials first
python test_api_client.py
```

### 3. Using curl
```bash
# Health check
curl http://localhost:8000/health

# Database discovery
curl -X POST "http://localhost:8000/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "database_config": {
      "server": "your-server.database.windows.net",
      "database": "your_database",
      "username": "your_username",
      "password": "your_password"
    },
    "max_tables": 10
  }'
```

## 🔧 **API Endpoints Summary**

| Endpoint | Method | Description | Use Case |
|----------|--------|-------------|----------|
| `/discover` | POST | Database discovery | Find tables and relationships |
| `/generate` | POST | Generate Q&A (sync) | Quick generation |
| `/generate-async` | POST | Generate Q&A (async) | Large datasets |
| `/jobs/{job_id}` | GET | Check job status | Monitor async jobs |
| `/download/{job_id}` | GET | Download dataset | Get results |

## 💡 **Key API Features**

✅ **Auto-Discovery**: Analyze whole database with `/discover`  
✅ **Flexible Input**: Specify tables or use `discover_all: true`  
✅ **Async Processing**: Background jobs for large operations  
✅ **Interactive Docs**: Built-in Swagger UI at `/docs`  
✅ **File Downloads**: Export results as JSON files  
✅ **Error Handling**: Detailed error messages and validation  

## 🎯 **Common Workflows**

### Workflow 1: Discover Then Generate
```bash
# 1. Start API
python start_api.py

# 2. Discover database (using interactive docs or curl)
# POST /discover with your DB config

# 3. Generate dataset using suggested tables
# POST /generate with discovered table names
```

### Workflow 2: Auto-Generate Everything  
```bash
# 1. Start API
python start_api.py

# 2. Auto-generate from whole database
# POST /generate with "discover_all": true
```

### Workflow 3: Async Generation for Large DBs
```bash
# 1. Start async job
# POST /generate-async

# 2. Monitor progress
# GET /jobs/{job_id}

# 3. Download results when complete
# GET /download/{job_id}
```

## 🔒 **Security Notes**

- 🔐 Never hardcode API keys in client code
- 🛡️ Use read-only database credentials
- 🌐 Configure CORS properly for production (see `api/main.py`)
- 📝 Sensitive data is excluded from logs

## 📚 **Complete Documentation**

- **API Guide**: `API_DOCUMENTATION.md` - Complete API reference
- **CLI Guide**: `WHOLE_DATABASE_GUIDE.md` - Command-line usage
- **Main README**: `README.md` - Project overview

## 🚀 **Production Deployment**

### Docker
```bash
# Build and run with Docker
docker build -t qna-generator-api .
docker run -p 8000:8000 qna-generator-api
```

### Docker Compose
```bash
# Run with Redis for job storage
docker-compose up -d
```

## ❓ **What's the Difference?**

| Feature | CLI (`generate_dataset.py`) | API (`start_api.py`) |
|---------|----------------------------|---------------------|
| **Usage** | Command-line scripts | Web applications |
| **Integration** | Shell scripts, cron jobs | Any programming language |
| **Interface** | Terminal commands | HTTP REST API |
| **Output** | Files on disk | JSON responses |
| **Async** | No | Yes (background jobs) |
| **Discovery** | `discover_database.py` | `/discover` endpoint |
| **Documentation** | `--help` flags | Interactive Swagger UI |

Both use the same underlying logic - choose based on your needs! 🎯
