#!/usr/bin/env python3
"""
Code RAG v11.0 - Complete End-to-End Demo
Demonstrates full workflow from GitHub project to intelligent search
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def print_header(title: str):
    print("\n" + "=" * 120)
    print(f"  {title}")
    print("=" * 120)


def print_section(title: str):
    print(f"\n{'-' * 120}")
    print(f"  {title}")
    print(f"{'-' * 120}")


def clone_github_project(repo_url: str, target_dir: Path) -> bool:
    """Clone a GitHub project with fallback"""
    print_section(f"📥 Cloning GitHub Project: {repo_url}")
    
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"  ✅ Successfully cloned repository")
            return True
        else:
            print(f"  ⚠️  Clone failed, creating mock project")
            return create_mock_project(target_dir)
    except Exception as e:
        print(f"  ⚠️  Error cloning, creating mock project: {e}")
        return create_mock_project(target_dir)


def create_mock_project(target_dir: Path) -> bool:
    """Create a realistic mock project for demo purposes"""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample Python files
    (target_dir / "src" / "myapp").mkdir(parents=True, exist_ok=True)
    
    # Main application file
    (target_dir / "src" / "myapp" / "main.py").write_text("""
\"\"\"
Main Application - Sample HTTP Client
\"\"\"
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class APIResponse:
    \"\"\"API response wrapper\"\"\"
    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str]


class APIClient:
    \"\"\"Simple API client for making HTTP requests\"\"\"
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = None
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> APIResponse:
        \"\"\"Make a GET request\"\"\"
        url = f"{self.base_url}{endpoint}"
        return self._make_request("GET", url, params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None,
             json_data: Optional[Dict] = None) -> APIResponse:
        \"\"\"Make a POST request\"\"\"
        url = f"{self.base_url}{endpoint}"
        return self._make_request("POST", url, data, json_data)
    
    def _make_request(self, method: str, url: str, 
                     params: Optional[Dict] = None,
                     json_data: Optional[Dict] = None) -> APIResponse:
        \"\"\"Internal method to make HTTP requests\"\"\"
        print(f"Making {method} request to {url}")
        
        # Mock implementation
        return APIResponse(
            status_code=200,
            data={"success": True, "method": method},
            headers={"Content-Type": "application/json"}
        )


def process_api_response(response: APIResponse) -> Dict[str, Any]:
    \"\"\"Process and validate API responses\"\"\"
    if response.status_code >= 400:
        raise ValueError(f"API error: {response.status_code}")
    return response.data


if __name__ == "__main__":
    client = APIClient("https://api.example.com")
    response = client.get("/v1/status")
    print(f"Status: {response.status_code}")
""")
    
    # Utility functions file
    (target_dir / "src" / "myapp" / "utils.py").write_text("""
\"\"\"
Utility Functions - Data processing and formatting
\"\"\"
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


def format_date(date_str: Optional[str] = None) -> str:
    \"\"\"Format date string to standardized format\"\"\"
    if date_str is None:
        return datetime.now().isoformat()
    return date_str


def sanitize_text(text: str, remove_extra_spaces: bool = True) -> str:
    \"\"\"Sanitize and clean text input\"\"\"
    if not text:
        return ""
    text = text.strip()
    if remove_extra_spaces:
        text = re.sub(r'\\s+', ' ', text)
    return text


def extract_json_objects(text: str) -> List[Dict]:
    \"\"\"Extract JSON objects from text content\"\"\"
    results = []
    stack = []
    
    for i, char in enumerate(text):
        if char == '{':
            stack.append(i)
        elif char == '}' and stack:
            start = stack.pop()
            try:
                json_str = text[start:i+1]
                obj = json.loads(json_str)
                results.append(obj)
            except:
                continue
    
    return results


def chunk_text(text: str, chunk_size: int = 1000, 
               overlap: int = 100) -> List[str]:
    \"\"\"Split text into overlapping chunks\"\"\"
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
    
    return chunks
""")
    
    # Test file
    (target_dir / "tests").mkdir(exist_ok=True)
    (target_dir / "tests" / "test_api_client.py").write_text("""
\"\"\"
Test Suite - API client and utilities testing
\"\"\"
import pytest
from src.myapp.main import APIClient, APIResponse
from src.myapp.utils import format_date, sanitize_text, chunk_text


def test_api_client_initialization():
    \"\"\"Test that API client initializes correctly\"\"\"
    client = APIClient("https://api.example.com")
    assert client.base_url == "https://api.example.com"
    assert client.timeout == 30


def test_api_get_request():
    \"\"\"Test GET request functionality\"\"\"
    client = APIClient("https://api.example.com")
    response = client.get("/test")
    assert response.status_code == 200
    assert isinstance(response.data, dict)


def test_sanitize_text():
    \"\"\"Test text sanitization\"\"\"
    assert sanitize_text("  Hello   World  ") == "Hello World"
    assert sanitize_text("") == ""


def test_chunk_text():
    \"\"\"Test text chunking\"\"\"
    text = "x" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)
""")
    
    # README
    (target_dir / "README.md").write_text("""
# MyApp - HTTP Client Library

A simple and elegant HTTP client library for Python applications.

## Features

- Easy-to-use API client
- JSON serialization support
- Response validation
- Text processing utilities
- Comprehensive test coverage

## Installation

```bash
pip install myapp
```

## Quick Start

```python
from myapp.main import APIClient

client = APIClient("https://api.example.com")
response = client.get("/v1/users")
print(response.data)
```

## API Reference

### APIClient

The main class for making HTTP requests.

**Methods:**
- `get(endpoint, params)` - Make GET requests
- `post(endpoint, data, json_data)` - Make POST requests

### Utilities

- `format_date()` - Format dates
- `sanitize_text()` - Clean and sanitize text
- `chunk_text()` - Split text into chunks

## License

MIT License
""")
    
    print(f"  ✅ Created mock project at {target_dir}")
    return True


def scan_project_files(project_dir: Path) -> List[Path]:
    """Scan and list project files"""
    print_section("🔍 Scanning Project Files")
    
    code_files = []
    
    for root, dirs, files in os.walk(str(project_dir)):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                  ('venv', '.venv', 'node_modules', '__pycache__', '.git')]
        
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.md', '.rst', '.txt')):
                file_path = Path(root) / file
                code_files.append(file_path)
    
    print(f"  Found {len(code_files)} code files:")
    for i, file_path in enumerate(code_files[:20]):
        rel_path = file_path.relative_to(project_dir)
        print(f"    {i+1}. {rel_path}")
    
    if len(code_files) > 20:
        print(f"    ... and {len(code_files) - 20} more")
    
    return code_files


def index_project_files(code_files: List[Path], project_dir: Path):
    """Index project files for search"""
    print_section("📊 Indexing Project Files")
    
    from code_rag.data_layer import CodeParser
    from code_rag.search_layer import BM25Index
    
    parser = CodeParser()
    bm25 = BM25Index()
    
    all_documents = []
    all_chunks = []
    
    for i, file_path in enumerate(code_files):
        try:
            doc = parser.parse_file(str(file_path))
            all_documents.append(doc)
            all_chunks.extend(doc.chunks)
            
            # Extract text for BM25
            for chunk in doc.chunks:
                if chunk.content:
                    rel_path = file_path.relative_to(project_dir)
                    bm25.add_documents([f"{rel_path}: {chunk.content}"])
            
            if (i + 1) % 10 == 0:
                print(f"    Indexed {i + 1}/{len(code_files)} files")
        except Exception as e:
            print(f"    ⚠️  Error indexing {file_path.name}: {e}")
    
    print(f"\n  ✅ Indexing complete!")
    print(f"    - Total documents: {len(all_documents)}")
    print(f"    - Total chunks: {len(all_chunks)}")
    
    return bm25


def demonstrate_search(bm25):
    """Demonstrate search capabilities"""
    print_section("🎯 Search Demonstration")
    
    test_queries = [
        "HTTP client API",
        "JSON processing",
        "text sanitization",
        "test cases",
        "date formatting",
    ]
    
    print(f"  Testing {len(test_queries)} search queries:")
    
    for query in test_queries:
        print(f"\n    Query: \"{query}\"")
        results = bm25.search(query, k=3)
        
        if results:
            for i, result in enumerate(results):
                preview = result.text[:80] if len(result.text) > 80 else result.text
                preview = preview.replace('\n', ' ')
                print(f"    {i+1}. [{result.score:.3f}] {preview}...")
        else:
            print(f"    No results found")


def main():
    print_header("🚀 Code RAG v11.0 - Complete End-to-End Demo")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Get project
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "demo_project"
        
        # Try real repo first, fallback to mock
        repo_url = "https://github.com/psf/requests.git"
        clone_github_project(repo_url, project_dir)
        
        # Step 2: Scan files
        code_files = scan_project_files(project_dir)
        
        if not code_files:
            print(f"  ❌ No code files found")
            return
        
        # Step 3: Index
        bm25 = index_project_files(code_files, project_dir)
        
        # Step 4: Search
        demonstrate_search(bm25)
    
    # Final summary
    print_header("✅ Demo Complete")
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n  📈 What we've demonstrated:")
    print(f"    1. ✅ Project acquisition (GitHub or mock)")
    print(f"    2. ✅ File scanning and discovery")
    print(f"    3. ✅ Code parsing and chunking")
    print(f"    4. ✅ BM25 search indexing")
    print(f"    5. ✅ Intelligent search queries")
    
    print(f"\n  🎯 Key features of Code RAG v11.0:")
    print(f"    - Production-ready modular architecture")
    print(f"    - Graceful degradation for missing dependencies")
    print(f"    - BM25 keyword search (fully functional)")
    print(f"    - Embedding integration (with sentence-transformers)")
    print(f"    - Vector search (with FAISS)")
    print(f"    - Multi-backend LLM support")


if __name__ == "__main__":
    main()
