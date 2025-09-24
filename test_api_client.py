"""
Simple test client for the GenAI SQL Test Data Generator API.
"""

import requests
import json
import time
from typing import Dict, Any

class QNAGeneratorClient:
    """Simple client for the QNA Generator API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client with API base URL."""
        self.base_url = base_url
        
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def discover_database(self, db_config: Dict[str, str], 
                         exclude_tables: list = None, 
                         max_tables: int = 10) -> Dict[str, Any]:
        """Discover database tables and relationships."""
        request_data = {
            "database_config": db_config,
            "exclude_tables": exclude_tables or [],
            "max_tables": max_tables
        }
        
        response = requests.post(f"{self.base_url}/discover", json=request_data)
        response.raise_for_status()
        return response.json()
    
    def generate_dataset(self, db_config: Dict[str, str], 
                        openai_config: Dict[str, str],
                        tables: list = None,
                        discover_all: bool = False,
                        generation_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate Q&A dataset synchronously."""
        request_data = {
            "database_config": db_config,
            "openai_config": openai_config,
            "generation_config": generation_config or {},
            "discover_all": discover_all
        }
        
        if tables:
            request_data["tables"] = tables
        
        response = requests.post(f"{self.base_url}/generate", json=request_data)
        response.raise_for_status()
        return response.json()
    
    def generate_dataset_async(self, db_config: Dict[str, str], 
                              openai_config: Dict[str, str],
                              tables: list = None,
                              discover_all: bool = False,
                              generation_config: Dict[str, Any] = None) -> str:
        """Start asynchronous Q&A dataset generation."""
        request_data = {
            "database_config": db_config,
            "openai_config": openai_config,
            "generation_config": generation_config or {},
            "discover_all": discover_all
        }
        
        if tables:
            request_data["tables"] = tables
        
        response = requests.post(f"{self.base_url}/generate-async", json=request_data)
        response.raise_for_status()
        result = response.json()
        return result["job_id"]
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of async job."""
        response = requests.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_job(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for async job to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            if status["status"] in ["completed", "failed"]:
                return status
            
            print(f"Job {job_id}: {status['status']} ({status['progress']:.1f}%)")
            time.sleep(5)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
    
    def download_dataset(self, job_id: str, filename: str = None) -> str:
        """Download generated dataset."""
        response = requests.get(f"{self.base_url}/download/{job_id}")
        response.raise_for_status()
        
        if not filename:
            filename = f"qna_dataset_{job_id}.json"
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        return filename


def main():
    """Example usage of the API client."""
    
    # Initialize client
    client = QNAGeneratorClient()
    
    # Check health
    print("🔍 Checking API health...")
    health = client.health_check()
    print(f"✅ API Status: {health['status']}")
    
    # Database configuration (replace with your actual values)
    db_config = {
        "server": "your-server.database.windows.net",
        "database": "your_database",
        "username": "your_username",
        "password": "your_password"
    }
    
    # OpenAI configuration (replace with your actual API key)
    openai_config = {
        "api_key": "sk-your-openai-api-key-here",
        "model": "gpt-4"
    }
    
    try:
        # Discover database
        print("\n🔍 Discovering database...")
        discovery = client.discover_database(
            db_config=db_config,
            exclude_tables=["sys", "temp", "log"],
            max_tables=8
        )
        
        if discovery["success"]:
            print(f"✅ Found {len(discovery['tables'])} tables")
            print(f"📊 Join potential: {discovery['join_potential']:.1f}%")
            
            # Use suggested tables for generation
            suggested_tables = discovery["suggested_tables"][:5]  # Top 5
            print(f"🎯 Using tables: {suggested_tables}")
            
            # Generate dataset
            print("\n🤖 Generating Q&A dataset...")
            generation_config = {
                "sample_size": 10,
                "min_questions": 15,
                "target_join_percentage": 40
            }
            
            result = client.generate_dataset(
                db_config=db_config,
                openai_config=openai_config,
                tables=suggested_tables,
                generation_config=generation_config
            )
            
            if result["success"]:
                dataset = result["dataset"]
                stats = result["statistics"]
                
                print(f"✅ Generated {stats['total_questions']} questions")
                print(f"🔗 Join questions: {stats['join_questions']} ({stats['join_percentage']:.1f}%)")
                
                # Save dataset
                filename = "api_generated_dataset.json"
                with open(filename, 'w') as f:
                    json.dump(dataset, f, indent=2)
                
                print(f"💾 Saved to {filename}")
                
                # Show sample questions
                print("\n📝 Sample Questions:")
                for i, qa in enumerate(dataset[:3], 1):
                    print(f"{i}. {qa['question']}")
                    print(f"   Answer: {qa['expected_answer']}\n")
            
            else:
                print(f"❌ Generation failed: {result['message']}")
        
        else:
            print(f"❌ Discovery failed: {discovery['message']}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Is the server running?")
        print("   Start with: python start_api.py")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
