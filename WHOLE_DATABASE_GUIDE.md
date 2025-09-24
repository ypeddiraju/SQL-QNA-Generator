# 🗄️ Whole Database Analysis Guide

## What You Asked For: "LLM into whole DB"

You want the LLM to analyze your **entire database** instead of just specific tables. Here's how to do it:

## 🚀 **NEW: Whole Database Analysis**

### Option 1: Interactive Discovery (Recommended)
```bash
# Discover all tables and choose interactively
python discover_database.py
```
This will:
1. 📊 Show you ALL tables in your database
2. 🔍 Let you select which ones to analyze  
3. 🔗 Show relationships between tables
4. 🚀 Generate the command to run

### Option 2: Automatic Analysis
```bash
# Analyze ALL tables automatically (first 10)
python discover_database.py --analyze-all --generate-dataset
```

### Option 3: Auto-Generate from Whole DB
```bash
# Skip discovery, just analyze everything
python generate_dataset.py --discover-all
```

## 📋 **Step-by-Step Guide**

### Step 1: Set Up Your Database Connection
Make sure your `.env` file has your database credentials:
```env
DB_SERVER=your-server-name
DB_DATABASE=your-database-name
DB_USERNAME=your-username
DB_PASSWORD=your-password
OPENAI_API_KEY=your-openai-key
```

### Step 2: Discover Your Database
```bash
python discover_database.py
```

**What this does:**
- 🔍 Finds ALL tables in your database
- 📊 Shows table structure and relationships  
- 🎯 Helps you select the most relevant tables
- 💡 Gives recommendations for better Q&A generation

**Example Output:**
```
🎯 Database Discovery Tool
==================================================

📊 Discovering all tables...
✅ Found 25 tables total

📋 Available Tables:
┌─────┬──────────────────┐
│  #  │ Table Name       │
├─────┼──────────────────┤
│  1  │ Customers        │
│  2  │ Orders           │
│  3  │ OrderItems       │
│  4  │ Products         │
│  5  │ Categories       │
│  6  │ Employees        │
│  7  │ Departments      │
│  8  │ Suppliers        │
└─────┴──────────────────┘

Select 2-10 tables for analysis:
Enter table numbers separated by commas (e.g., 1,3,5)
Or enter 'all' to select all tables (limited to first 10)
Your selection: 1,2,3,4,5
```

### Step 3: Review Analysis
The tool will show you:
```
📊 Database Analysis Results
==================================================

🗂️  Selected Tables (5):
  • Customers (8 columns)
  • Orders (6 columns)  
  • OrderItems (5 columns)
  • Products (7 columns)
  • Categories (3 columns)

🔗 Foreign Key Relationships (4):
  • Orders.CustomerID → Customers.CustomerID
  • OrderItems.OrderID → Orders.OrderID
  • OrderItems.ProductID → Products.ProductID
  • Products.CategoryID → Categories.CategoryID
  ✅ Good join potential (80%)

💡 Recommendations:
  • Review the relationships above to ensure they make sense
  • The generator will create ~40% join-based questions and 60% single-table questions
```

### Step 4: Generate Q&A Dataset
```bash
# Use the suggested command from discovery
python generate_dataset.py --tables "Customers,Orders,OrderItems,Products,Categories"
```

## 🎯 **Why This Approach?**

### The Problem with "Whole DB"
- Most databases have 20-100+ tables
- LLMs have token limits (~8K-32K tokens)
- Too many tables = poor quality questions
- System tables, logs, temp tables aren't useful for Q&A

### The Smart Solution  
- 🔍 **Discovery**: Find all tables automatically
- 🎯 **Selection**: Choose the most relevant ones (2-10 tables)
- 🔗 **Analysis**: Focus on tables with relationships
- 🤖 **Generation**: Create high-quality Q&A with joins

## 🚀 **Quick Commands for Your Use Case**

```bash
# 1. See what's in your database
python discover_database.py

# 2. Analyze everything automatically  
python discover_database.py --analyze-all

# 3. Generate dataset from top 10 tables
python generate_dataset.py --discover-all

# 4. Exclude system/temp tables
python discover_database.py --exclude-tables "sys,temp,log,audit"
```

## 🔧 **Advanced Options**

### Control Table Selection
```bash
# Analyze all but limit to 8 tables max
python discover_database.py --analyze-all --max-tables 8

# Require minimum 3 tables
python discover_database.py --min-tables 3 --max-tables 12

# Exclude specific tables
python discover_database.py --exclude-tables "SystemLog,TempData,Audit"
```

### Direct Generation
```bash
# Generate from whole DB with custom settings
python generate_dataset.py \
  --discover-all \
  --sample-size 20 \
  --output "whole_db_dataset.json"
```

## 📊 **What You Get**

The LLM will analyze your **entire selected database structure** and create questions like:

```json
[
  {
    "question": "How many customers have placed more than 5 orders?",
    "expected_answer": "12"
  },
  {
    "question": "What is the total revenue from Electronics category products?", 
    "expected_answer": "45780.50"
  },
  {
    "question": "Which product has been ordered the most times?",
    "expected_answer": "Wireless Mouse"
  },
  {
    "question": "List all customers who have never placed an order.",
    "expected_answer": "Sarah Johnson, Mike Davis"
  }
]
```

## 🎉 **Try It Now!**

1. **Discover your database:**
   ```bash
   python discover_database.py
   ```

2. **Or just analyze everything:**
   ```bash
   python generate_dataset.py --discover-all
   ```

This gives you the "LLM into whole DB" functionality you wanted! 🚀
