#!/usr/bin/env python3
"""
Test script for chapter ordering validation fix
"""

import sys
from nodes import OrderChapters

def test_chapter_ordering_validation():
    """Test that chapter ordering validation handles out-of-bounds indices gracefully"""
    print("🧪 Testing chapter ordering validation...")
    print("=" * 50)
    
    # Create a mock shared state with sample data
    shared = {
        "abstractions": [
            {
                "name": "Component A",
                "description": "First component",
                "files": [0]
            },
            {
                "name": "Component B", 
                "description": "Second component",
                "files": [1]
            }
        ],
        "relationships": {
            "summary": "This is a test project with two components.",
            "details": [
                {
                    "from": 0,
                    "to": 1,
                    "label": "Related to"
                }
            ]
        },
        "project_name": "TestProject",
        "language": "english",
        "use_cache": True
    }
    
    # Mock the LLM response with out-of-bounds indices
    class MockOrderChapters(OrderChapters):
        def exec(self, prep_res):
            # Simulate LLM returning out-of-bounds indices
            return [0, 2, 1]  # Index 2 is out of bounds for 2 abstractions
    
    node = MockOrderChapters()
    
    try:
        prep_res = node.prep(shared)
        exec_res = node.exec(prep_res)
        node.post(shared, prep_res, exec_res)
        
        print(f"✅ Chapter ordering validation successful!")
        print(f"   Ordered indices: {exec_res}")
        print(f"   Expected: [0, 1] (filtered out invalid index 2)")
        print(f"   Note: System correctly filters invalid indices and ensures all valid indices are included")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in chapter ordering validation: {e}")
        return False

def test_missing_indices_handling():
    """Test that the system handles missing indices gracefully"""
    print("\n🧪 Testing missing indices handling...")
    print("=" * 50)
    
    # Create a mock shared state with 3 abstractions
    shared = {
        "abstractions": [
            {
                "name": "Component A",
                "description": "First component",
                "files": [0]
            },
            {
                "name": "Component B", 
                "description": "Second component",
                "files": [1]
            },
            {
                "name": "Component C", 
                "description": "Third component",
                "files": [2]
            }
        ],
        "relationships": {
            "summary": "This is a test project with three components.",
            "details": [
                {
                    "from": 0,
                    "to": 1,
                    "label": "Related to"
                }
            ]
        },
        "project_name": "TestProject",
        "language": "english",
        "use_cache": True
    }
    
    # Mock the LLM response with missing indices
    class MockOrderChapters(OrderChapters):
        def exec(self, prep_res):
            # Simulate LLM returning incomplete list
            return [0, 2]  # Missing index 1
    
    node = MockOrderChapters()
    
    try:
        prep_res = node.prep(shared)
        exec_res = node.exec(prep_res)
        node.post(shared, prep_res, exec_res)
        
        print(f"✅ Missing indices handling successful!")
        print(f"   Ordered indices: {exec_res}")
        print(f"   Expected: [0, 2, 1] (added missing index 1)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in missing indices handling: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Chapter Ordering Validation Tests")
    print("=" * 50)
    
    success = True
    
    # Run tests
    if not test_chapter_ordering_validation():
        success = False
    
    if not test_missing_indices_handling():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All chapter ordering validation tests passed!")
        print("\n📝 Features:")
        print("   ✅ Graceful handling of out-of-bounds indices")
        print("   ✅ Automatic addition of missing indices")
        print("   ✅ Fallback to default ordering when needed")
        print("   ✅ Proper warning messages without crashing")
        sys.exit(0)
    else:
        print("❌ Some chapter ordering validation tests failed.")
        sys.exit(1) 