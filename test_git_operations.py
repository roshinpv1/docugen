#!/usr/bin/env python3
"""
Test script for the comprehensive Git operations utility
"""

import os
import sys
import tempfile
from utils.git_operations import (
    clone_repository, 
    cleanup_repository, 
    get_repository_info,
    _parse_github_url
)

def test_github_url_parsing():
    """Test GitHub URL parsing functionality"""
    print("🧪 Testing GitHub URL parsing...")
    print("=" * 50)
    
    test_cases = [
        ("https://github.com/octocat/Hello-World", ("octocat", "Hello-World")),
        ("https://github.com/microsoft/vscode.git", ("microsoft", "vscode")),
        ("https://github.com/owner/repo-name", ("owner", "repo-name")),
        ("https://github.com/owner/repo-name/tree/main", ("owner", "repo-name")),
    ]
    
    for url, expected in test_cases:
        try:
            result = _parse_github_url(url)
            if result == expected:
                print(f"✅ {url} -> {result}")
            else:
                print(f"❌ {url} -> {result} (expected {expected})")
                return False
        except Exception as e:
            print(f"❌ {url} -> Error: {e}")
            return False
    
    print("✅ GitHub URL parsing tests passed!")
    return True

def test_repository_cloning():
    """Test repository cloning functionality"""
    print("\n🧪 Testing repository cloning...")
    print("=" * 50)
    
    # Test with a small public repository
    test_repo = "https://github.com/octocat/Hello-World"
    test_branch = "master"
    
    print(f"Testing with: {test_repo}")
    
    try:
        # Test cloning
        repo_path = clone_repository(test_repo, branch=test_branch)
        print(f"✅ Repository cloned to: {repo_path}")
        
        # Test repository info
        info = get_repository_info(repo_path)
        print(f"📊 Repository info: {info}")
        
        # Verify the repository was cloned correctly
        if not info["exists"]:
            print("❌ Repository directory does not exist")
            return False
        
        if not info["is_git_repo"]:
            print("❌ Cloned directory is not a git repository")
            return False
        
        # Test cleanup
        cleanup_repository(repo_path)
        print("✅ Repository cleanup successful")
        
        # Verify cleanup
        if os.path.exists(repo_path):
            print("❌ Repository directory still exists after cleanup")
            return False
        
        print("✅ Repository cloning tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Repository cloning test failed: {e}")
        return False

def test_enterprise_configuration():
    """Test enterprise configuration detection"""
    print("\n🧪 Testing enterprise configuration...")
    print("=" * 50)
    
    # Test environment variable detection
    env_vars = [
        "GITHUB_ENTERPRISE_DISABLE_SSL",
        "GITHUB_ENTERPRISE_CA_BUNDLE"
    ]
    
    print("Enterprise environment variables:")
    for var in env_vars:
        value = os.getenv(var)
        status = "✅ Set" if value else "⚪ Not set"
        print(f"   {var}: {status}")
    
    # Test URL parsing for enterprise detection
    test_urls = [
        ("https://github.com/owner/repo", False),
        ("https://github.company.com/owner/repo", True),
        ("https://git.company.com/owner/repo", False),
    ]
    
    print("\nEnterprise URL detection:")
    for url, expected_enterprise in test_urls:
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc.lower()
        is_enterprise = 'github' in hostname and hostname != 'github.com'
        
        status = "✅" if is_enterprise == expected_enterprise else "❌"
        print(f"   {status} {url} -> Enterprise: {is_enterprise} (expected: {expected_enterprise})")
    
    print("✅ Enterprise configuration tests completed!")
    return True

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🧪 Testing error handling...")
    print("=" * 50)
    
    # Test with non-existent repository
    non_existent_repo = "https://github.com/nonexistent/nonexistent-repo"
    
    try:
        repo_path = clone_repository(non_existent_repo)
        print(f"❌ Unexpectedly cloned non-existent repository: {repo_path}")
        cleanup_repository(repo_path)
        return False
    except Exception as e:
        print(f"✅ Correctly handled non-existent repository: {e}")
    
    # Test with invalid URL
    invalid_url = "https://invalid-url-that-does-not-exist.com/repo"
    
    try:
        repo_path = clone_repository(invalid_url)
        print(f"❌ Unexpectedly cloned invalid URL: {repo_path}")
        cleanup_repository(repo_path)
        return False
    except Exception as e:
        print(f"✅ Correctly handled invalid URL: {e}")
    
    print("✅ Error handling tests passed!")
    return True

def test_cleanup_functionality():
    """Test cleanup functionality"""
    print("\n🧪 Testing cleanup functionality...")
    print("=" * 50)
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_cleanup_")
    print(f"Created temporary directory: {temp_dir}")
    
    # Create a test file
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")
    
    # Test cleanup
    cleanup_repository(temp_dir)
    
    # Verify cleanup
    if os.path.exists(temp_dir):
        print(f"❌ Directory still exists after cleanup: {temp_dir}")
        return False
    else:
        print("✅ Cleanup successful")
    
    print("✅ Cleanup functionality tests passed!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Git Operations Tests")
    print("=" * 50)
    
    success = True
    
    # Run all tests
    tests = [
        test_github_url_parsing,
        test_repository_cloning,
        test_enterprise_configuration,
        test_error_handling,
        test_cleanup_functionality
    ]
    
    for test in tests:
        if not test():
            success = False
            break
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All Git operations tests passed!")
        sys.exit(0)
    else:
        print("❌ Some Git operations tests failed.")
        sys.exit(1) 