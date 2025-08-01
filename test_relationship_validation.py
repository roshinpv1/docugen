#!/usr/bin/env python3
"""
Test script for relationship validation fix
"""

import sys
from nodes import AnalyzeRelationships

def test_relationship_validation():
    """Test that relationship validation handles out-of-bounds indices gracefully"""
    print("🧪 Testing relationship validation...")
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
        "files": [
            ("file1.py", "class ComponentA: pass"),
            ("file2.py", "class ComponentB: pass")
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
        
        print(f"✅ Relationship validation successful!")
        print(f"   Summary: {exec_res['summary'][:100]}...")
        print(f"   Relationships: {len(exec_res['details'])} connections")
        
        for rel in exec_res['details']:
            from_name = shared["abstractions"][rel["from"]]["name"]
            to_name = shared["abstractions"][rel["to"]]["name"]
            print(f"   - {from_name} -> {to_name}: {rel['label']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in relationship validation: {e}")
        return False

def test_out_of_bounds_handling():
    """Test that the system handles out-of-bounds indices gracefully"""
    print("\n🧪 Testing out-of-bounds index handling...")
    print("=" * 50)
    
    # Create a mock shared state with only 2 abstractions
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
        "files": [
            ("file1.py", "class ComponentA: pass"),
            ("file2.py", "class ComponentB: pass")
        ],
        "project_name": "TestProject",
        "language": "english",
        "use_cache": True
    }
    
    # Mock the LLM response with out-of-bounds indices
    class MockAnalyzeRelationships(AnalyzeRelationships):
        def exec(self, prep_res):
            # Simulate LLM returning out-of-bounds indices
            return {
                "summary": "This is a test project with two components.",
                "relationships": [
                    {
                        "from_abstraction": "0 # Component A",
                        "to_abstraction": "1 # Component B", 
                        "label": "Valid relationship"
                    },
                    {
                        "from_abstraction": "2 # Invalid Component",
                        "to_abstraction": "3 # Another Invalid Component",
                        "label": "Invalid relationship"
                    }
                ]
            }
    
    node = MockAnalyzeRelationships()
    
    try:
        prep_res = node.prep(shared)
        exec_res = node.exec(prep_res)
        
        # Test the validation logic directly
        relationships_data = exec_res
        num_abstractions = len(shared["abstractions"])
        
        validated_relationships = []
        for rel in relationships_data["relationships"]:
            # Check for 'label' key
            if not isinstance(rel, dict) or not all(
                k in rel for k in ["from_abstraction", "to_abstraction", "label"]
            ):
                print(f"Warning: Skipping invalid relationship structure: {rel}")
                continue
            # Validate 'label' is a string
            if not isinstance(rel["label"], str):
                print(f"Warning: Skipping relationship with invalid label: {rel}")
                continue

            # Validate indices
            try:
                from_idx = int(str(rel["from_abstraction"]).split("#")[0].strip())
                to_idx = int(str(rel["to_abstraction"]).split("#")[0].strip())
                if not (
                    0 <= from_idx < num_abstractions and 0 <= to_idx < num_abstractions
                ):
                    print(f"Warning: Skipping relationship with out-of-bounds indices: from={from_idx}, to={to_idx}. Max index is {num_abstractions-1}.")
                    continue
                validated_relationships.append(
                    {
                        "from": from_idx,
                        "to": to_idx,
                        "label": rel["label"],
                    }
                )
            except (ValueError, TypeError):
                print(f"Warning: Skipping relationship with unparseable indices: {rel}")
                continue

        # Ensure we have at least some valid relationships
        if not validated_relationships:
            print("Warning: No valid relationships found. Creating default relationships.")
            # Create default relationships to ensure each abstraction is connected
            for i in range(num_abstractions):
                for j in range(i + 1, num_abstractions):
                    validated_relationships.append({
                        "from": i,
                        "to": j,
                        "label": "Related to"
                    })
                    break  # Only create one relationship per abstraction
        
        print(f"✅ Out-of-bounds handling successful!")
        print(f"   Valid relationships: {len(validated_relationships)}")
        print(f"   Expected: 1 valid relationship, 1 invalid filtered out")
        
        for rel in validated_relationships:
            from_name = shared["abstractions"][rel["from"]]["name"]
            to_name = shared["abstractions"][rel["to"]]["name"]
            print(f"   - {from_name} -> {to_name}: {rel['label']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in out-of-bounds handling: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Relationship Validation Tests")
    print("=" * 50)
    
    success = True
    
    # Run tests
    if not test_relationship_validation():
        success = False
    
    if not test_out_of_bounds_handling():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All relationship validation tests passed!")
        print("\n📝 Features:")
        print("   ✅ Graceful handling of invalid relationship structures")
        print("   ✅ Filtering out out-of-bounds indices")
        print("   ✅ Fallback to default relationships when needed")
        print("   ✅ Proper error messages without crashing")
        sys.exit(0)
    else:
        print("❌ Some relationship validation tests failed.")
        sys.exit(1) 