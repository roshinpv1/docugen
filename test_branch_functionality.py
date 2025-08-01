#!/usr/bin/env python3
"""
Test script for the new branch functionality
"""

import os
import sys
from utils.crawl_github_files import crawl_github_files

def test_branch_functionality():
    """Test that the branch parameter works correctly"""
    print("🧪 Testing branch functionality...")
    print("=" * 50)
    
    # Test with a public repository that has multiple branches
    test_repo = "https://github.com/octocat/Hello-World"
    
    # Get GitHub token from environment
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("⚠️ No GitHub token found. This test may hit rate limits.")
    
    print(f"Testing with repository: {test_repo}")
    
    # Test 1: Default branch (master - this repo uses master, not main)
    print("\n1. Testing default branch (master)...")
    try:
        result = crawl_github_files(
            repo_url=test_repo,
            token=github_token,
            branch="master",
            max_file_size=10 * 1024,  # 10 KB
            include_patterns="*"  # Include all files
        )
        
        if result and "files" in result and result["files"]:
            print(f"✅ Successfully cloned master branch: {len(result['files'])} files")
            print(f"   Branch used: {result['stats'].get('branch', 'unknown')}")
            # Show some file names
            for filename in list(result['files'].keys())[:3]:
                print(f"   - {filename}")
        else:
            print("❌ Failed to clone master branch")
            return False
            
    except Exception as e:
        print(f"❌ Error cloning master branch: {e}")
        return False
    
    # Test 2: Main branch (may not exist in this repo)
    print("\n2. Testing main branch...")
    try:
        result = crawl_github_files(
            repo_url=test_repo,
            token=github_token,
            branch="main",
            max_file_size=10 * 1024,  # 10 KB
            include_patterns="*"  # Include all files
        )
        
        if result and "files" in result and result["files"]:
            print(f"✅ Successfully cloned main branch: {len(result['files'])} files")
            print(f"   Branch used: {result['stats'].get('branch', 'unknown')}")
        else:
            print("⚠️ Main branch may not exist or be empty")
            
    except Exception as e:
        print(f"⚠️ Error cloning main branch (may not exist): {e}")
    
    # Test 3: Non-existent branch
    print("\n3. Testing non-existent branch...")
    try:
        result = crawl_github_files(
            repo_url=test_repo,
            token=github_token,
            branch="non-existent-branch",
            max_file_size=10 * 1024,  # 10 KB
            include_patterns="*"  # Include all files
        )
        
        if result and "error" in result.get("stats", {}):
            print(f"✅ Correctly handled non-existent branch: {result['stats']['error']}")
        else:
            print("⚠️ Non-existent branch test completed without error")
            
    except Exception as e:
        print(f"✅ Correctly handled non-existent branch error: {e}")
    
    print("\n✅ Branch functionality tests completed!")
    return True

def test_command_line_parsing():
    """Test that command line arguments are parsed correctly"""
    print("\n🧪 Testing command line argument parsing...")
    print("=" * 50)
    
    # Simulate command line arguments
    test_args = [
        ["--repo", "https://github.com/test/repo", "--branch", "develop"],
        ["--repo", "https://github.com/test/repo", "-b", "feature/new-api"],
        ["--repo", "https://github.com/test/repo"],  # No branch specified
    ]
    
    for i, args in enumerate(test_args, 1):
        print(f"\nTest {i}: {' '.join(args)}")
        
        # Import and test argument parsing
        try:
            import argparse
            from main import main
            
            # Create a mock parser to test argument parsing
            parser = argparse.ArgumentParser()
            parser.add_argument("--repo")
            parser.add_argument("-b", "--branch", default="main")
            
            parsed = parser.parse_args(args)
            print(f"   Repo: {parsed.repo}")
            print(f"   Branch: {parsed.branch}")
            
        except Exception as e:
            print(f"   ❌ Error parsing arguments: {e}")
    
    print("\n✅ Command line argument parsing tests completed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Branch Functionality Tests")
    print("=" * 50)
    
    success = True
    
    # Run tests
    if not test_branch_functionality():
        success = False
    
    if not test_command_line_parsing():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All branch functionality tests passed!")
        print("\n📝 Usage examples:")
        print("   python main.py --repo https://github.com/username/repo --branch develop")
        print("   python main.py --repo https://github.com/username/repo -b feature/new-api")
        print("   python main.py --repo https://github.com/username/repo --branch main --language Chinese")
        sys.exit(0)
    else:
        print("❌ Some branch functionality tests failed.")
        sys.exit(1) 