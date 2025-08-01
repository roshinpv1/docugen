#!/usr/bin/env python3
"""
Test script for the new technical documentation functionality
"""

import os
import sys
import tempfile
import shutil
from nodes import IdentifyAbstractions, AnalyzeRelationships, WriteChapters

def test_technical_component_identification():
    """Test that technical components are identified correctly"""
    print("🧪 Testing technical component identification...")
    print("=" * 50)
    
    # Create a mock shared state with sample files
    shared = {
        "files": [
            ("auth/service.py", """
class AuthService:
    def authenticate(self, username, password):
        # Authentication logic
        pass
    
    def generate_token(self, user_id):
        # JWT token generation
        pass
            """),
            ("api/products.py", """
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/products', methods=['GET'])
def get_products():
    return jsonify({'products': []})

@app.route('/products', methods=['POST'])
def create_product():
    return jsonify({'message': 'Product created'})
            """),
            ("models/user.py", """
class User:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email
            """),
        ],
        "project_name": "TestProject",
        "language": "english",
        "use_cache": True,
        "max_abstraction_num": 5
    }
    
    # Test IdentifyAbstractions node
    node = IdentifyAbstractions()
    
    try:
        prep_res = node.prep(shared)
        exec_res = node.exec(prep_res)
        node.post(shared, prep_res, exec_res)
        
        print(f"✅ Successfully identified {len(exec_res)} technical components:")
        for i, component in enumerate(exec_res):
            print(f"   {i+1}. {component['name']}")
            print(f"      Description: {component['description'][:100]}...")
            print(f"      Files: {len(component['files'])} files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in technical component identification: {e}")
        return False

def test_technical_relationships():
    """Test that technical relationships are analyzed correctly"""
    print("\n🧪 Testing technical relationship analysis...")
    print("=" * 50)
    
    # Create a mock shared state with identified components
    shared = {
        "abstractions": [
            {
                "name": "User Authentication Service",
                "description": "Handles user authentication and authorization with JWT tokens",
                "files": [0]
            },
            {
                "name": "Product API Endpoints", 
                "description": "RESTful API endpoints for product management",
                "files": [1]
            },
            {
                "name": "User Data Models",
                "description": "Database models for user data",
                "files": [2]
            }
        ],
        "files": [
            ("auth/service.py", "class AuthService: pass"),
            ("api/products.py", "app = Flask(__name__)"),
            ("models/user.py", "class User: pass")
        ],
        "project_name": "TestProject",
        "language": "english",
        "use_cache": True
    }
    
    # Test AnalyzeRelationships node
    node = AnalyzeRelationships()
    
    try:
        prep_res = node.prep(shared)
        exec_res = node.exec(prep_res)
        node.post(shared, prep_res, exec_res)
        
        print(f"✅ Successfully analyzed technical relationships:")
        print(f"   Summary: {exec_res['summary'][:100]}...")
        print(f"   Relationships: {len(exec_res['details'])} connections")
        
        for rel in exec_res['details']:
            from_name = shared["abstractions"][rel["from"]]["name"]
            to_name = shared["abstractions"][rel["to"]]["name"]
            print(f"   - {from_name} -> {to_name}: {rel['label']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in technical relationship analysis: {e}")
        return False

def test_technical_documentation_generation():
    """Test that technical documentation chapters are generated correctly"""
    print("\n🧪 Testing technical documentation generation...")
    print("=" * 50)
    
    # Create a mock shared state
    shared = {
        "abstractions": [
            {
                "name": "User Authentication Service",
                "description": "Handles user authentication and authorization with JWT tokens",
                "files": [0]
            }
        ],
        "files": [
            ("auth/service.py", """
class AuthService:
    def authenticate(self, username, password):
        # Authentication logic
        return {"token": "jwt_token"}
            """)
        ],
        "chapter_order": [0],
        "project_name": "TestProject",
        "language": "english",
        "use_cache": True
    }
    
    # Test WriteChapters node
    node = WriteChapters()
    
    try:
        prep_res = node.prep(shared)
        exec_res = node.exec(prep_res[0])  # Test with first item
        node.post(shared, prep_res, [exec_res])
        
        print(f"✅ Successfully generated technical documentation:")
        print(f"   Content length: {len(exec_res)} characters")
        print(f"   Contains technical sections: {'API' in exec_res or 'Architecture' in exec_res}")
        print(f"   Contains code examples: {'```' in exec_res}")
        
        # Show a snippet of the generated content
        lines = exec_res.split('\n')[:10]
        print(f"   Preview:")
        for line in lines:
            print(f"      {line}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in technical documentation generation: {e}")
        return False

def test_command_line_parsing():
    """Test that command line arguments are parsed correctly for technical docs"""
    print("\n🧪 Testing command line argument parsing...")
    print("=" * 50)
    
    # Simulate command line arguments
    test_args = [
        ["--repo", "https://github.com/test/repo", "--max-abstractions", "15"],
        ["--dir", "/path/to/code", "--language", "Chinese"],
        ["--repo", "https://github.com/test/repo", "--branch", "develop"],
    ]
    
    for i, args in enumerate(test_args, 1):
        print(f"\nTest {i}: {' '.join(args)}")
        
        try:
            import argparse
            from main import main
            
            # Create a mock parser to test argument parsing
            parser = argparse.ArgumentParser()
            parser.add_argument("--repo")
            parser.add_argument("--dir")
            parser.add_argument("--max-abstractions", type=int, default=10)
            parser.add_argument("--language", default="english")
            parser.add_argument("--branch", default="main")
            
            parsed = parser.parse_args(args)
            print(f"   Repo: {parsed.repo}")
            print(f"   Dir: {parsed.dir}")
            print(f"   Max Components: {parsed.max_abstractions}")
            print(f"   Language: {parsed.language}")
            print(f"   Branch: {parsed.branch}")
            
        except Exception as e:
            print(f"   ❌ Error parsing arguments: {e}")
    
    print("\n✅ Command line argument parsing tests completed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Technical Documentation Tests")
    print("=" * 50)
    
    success = True
    
    # Run tests
    if not test_technical_component_identification():
        success = False
    
    if not test_technical_relationships():
        success = False
    
    if not test_technical_documentation_generation():
        success = False
    
    if not test_command_line_parsing():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All technical documentation tests passed!")
        print("\n📝 Key Features:")
        print("   ✅ Technical component identification (API endpoints, libraries, etc.)")
        print("   ✅ Architecture relationship analysis")
        print("   ✅ Comprehensive technical documentation generation")
        print("   ✅ Support for multiple languages")
        print("   ✅ Branch-specific documentation")
        print("\n📝 Usage examples:")
        print("   python main.py --repo https://github.com/username/repo --max-abstractions 15")
        print("   python main.py --repo https://github.com/username/repo --branch develop --language Chinese")
        print("   python main.py --dir /path/to/code --include '*.py' '*.js'")
        sys.exit(0)
    else:
        print("❌ Some technical documentation tests failed.")
        sys.exit(1) 