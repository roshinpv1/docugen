# Git Operations Utility Guide

This guide explains how to use the comprehensive Git operations utility that handles repository cloning and management with enterprise support.

## Overview

The Git operations utility provides a unified interface for cloning repositories from various sources including GitHub.com, GitHub Enterprise, and other Git servers. It automatically selects the best method (Git clone vs GitHub API) based on the repository type and provides comprehensive error handling and enterprise support.

## Features

### 🏢 **Enterprise Support**
- **GitHub Enterprise**: Automatic detection and configuration
- **SSL Certificate Handling**: Support for self-signed certificates and custom CA bundles
- **Network Configuration**: Enterprise-friendly network settings
- **Authentication**: Token-based authentication for private repositories

### 🔄 **Smart Method Selection**
- **GitHub.com**: Tries Git clone first (unlimited, no rate limits), falls back to API
- **GitHub Enterprise**: Tries API first (better for enterprise networks), falls back to Git clone
- **Other Git Servers**: Uses Git clone exclusively

### 🛡️ **Error Handling**
- **SSL Certificate Errors**: Automatic retry with SSL verification disabled
- **Authentication Errors**: Clear error messages for token issues
- **Network Errors**: Retry logic with exponential backoff
- **Repository Errors**: Specific handling for missing repositories

### 🧹 **Resource Management**
- **Automatic Cleanup**: Temporary directories are cleaned up on failure
- **Memory Efficient**: Streaming downloads for large repositories
- **Timeout Handling**: Configurable timeouts for different operations

## Usage

### Basic Usage

```python
from utils.git_operations import clone_repository, cleanup_repository

# Clone a repository
repo_path = clone_repository(
    repo_url="https://github.com/owner/repo",
    branch="main",
    github_token="your-token"
)

# Use the repository
print(f"Repository cloned to: {repo_path}")

# Clean up when done
cleanup_repository(repo_path)
```

### Advanced Usage

```python
from utils.git_operations import clone_repository, get_repository_info

# Clone with specific branch and target directory
repo_path = clone_repository(
    repo_url="https://github.com/owner/repo",
    branch="develop",
    github_token="your-token",
    target_dir="/path/to/target"
)

# Get repository information
info = get_repository_info(repo_path)
print(f"Branch: {info['current_branch']}")
print(f"Commit: {info['commit_hash']}")
```

## Configuration

### Environment Variables

#### GitHub Enterprise Configuration

```bash
# Disable SSL verification (common in enterprise environments)
export GITHUB_ENTERPRISE_DISABLE_SSL=true

# Use custom CA bundle for SSL verification
export GITHUB_ENTERPRISE_CA_BUNDLE=/path/to/ca-bundle.pem

# GitHub token for authentication
export GITHUB_TOKEN=your-github-token
```

#### SSL Configuration

The utility supports three SSL verification modes:

1. **Default SSL Verification**: Uses system CA certificates
2. **Custom CA Bundle**: Uses a custom certificate authority bundle
3. **SSL Verification Disabled**: Skips SSL verification (for self-signed certificates)

### Enterprise-Specific Settings

For GitHub Enterprise environments, the utility automatically:

- Detects enterprise URLs (any GitHub hostname other than `github.com`)
- Configures SSL settings based on environment variables
- Uses enterprise-specific API endpoints
- Handles enterprise network configurations

## Repository Types

### GitHub.com Repositories

```python
# Public repository
repo_path = clone_repository("https://github.com/octocat/Hello-World")

# Private repository (requires token)
repo_path = clone_repository(
    "https://github.com/owner/private-repo",
    github_token="your-token"
)
```

### GitHub Enterprise Repositories

```python
# Enterprise repository
repo_path = clone_repository(
    "https://github.company.com/owner/repo",
    github_token="your-enterprise-token"
)
```

### Other Git Servers

```python
# GitLab, Bitbucket, or other Git servers
repo_path = clone_repository("https://gitlab.com/owner/repo")
repo_path = clone_repository("https://bitbucket.org/owner/repo")
```

## Error Handling

### Common Error Scenarios

#### SSL Certificate Errors

```python
try:
    repo_path = clone_repository("https://github.company.com/owner/repo")
except Exception as e:
    if "SSL certificate" in str(e):
        # Set environment variable and retry
        os.environ['GITHUB_ENTERPRISE_DISABLE_SSL'] = 'true'
        repo_path = clone_repository("https://github.company.com/owner/repo")
```

#### Authentication Errors

```python
try:
    repo_path = clone_repository("https://github.com/owner/private-repo")
except Exception as e:
    if "authentication failed" in str(e):
        print("Please provide a valid GitHub token")
```

#### Repository Not Found

```python
try:
    repo_path = clone_repository("https://github.com/owner/nonexistent-repo")
except Exception as e:
    if "repository not found" in str(e):
        print("Repository does not exist or access denied")
```

## API Reference

### Functions

#### `clone_repository(repo_url, branch="main", github_token=None, target_dir=None)`

Clone a repository using the best available method.

**Parameters:**
- `repo_url` (str): Repository URL
- `branch` (str): Branch to checkout (default: "main")
- `github_token` (str, optional): GitHub token for private repositories
- `target_dir` (str, optional): Target directory (creates temp dir if None)

**Returns:**
- `str`: Path to cloned repository

**Raises:**
- `Exception`: If cloning fails

#### `cleanup_repository(repo_path)`

Clean up a cloned repository.

**Parameters:**
- `repo_path` (str): Path to repository directory

#### `get_repository_info(repo_path)`

Get basic information about a repository.

**Parameters:**
- `repo_path` (str): Path to repository directory

**Returns:**
- `dict`: Repository information including:
  - `path`: Repository path
  - `exists`: Whether directory exists
  - `is_git_repo`: Whether it's a Git repository
  - `current_branch`: Current branch name
  - `commit_hash`: Current commit hash
  - `remote_url`: Remote repository URL

## Testing

You can test the Git operations utility using the provided test script:

```bash
python test_git_operations.py
```

This will test:
1. GitHub URL parsing
2. Repository cloning
3. Enterprise configuration detection
4. Error handling
5. Cleanup functionality

## Best Practices

### 1. **Always Clean Up**
```python
repo_path = None
try:
    repo_path = clone_repository("https://github.com/owner/repo")
    # Use the repository
finally:
    if repo_path:
        cleanup_repository(repo_path)
```

### 2. **Handle Enterprise Environments**
```python
# Set enterprise environment variables
os.environ['GITHUB_ENTERPRISE_DISABLE_SSL'] = 'true'
os.environ['GITHUB_TOKEN'] = 'your-token'

repo_path = clone_repository("https://github.company.com/owner/repo")
```

### 3. **Use Appropriate Timeouts**
The utility uses reasonable defaults, but you can adjust timeouts for your environment:
- Git clone: Uses Git's default timeout
- API download: 30s connect, 300s read timeout

### 4. **Error Handling**
```python
try:
    repo_path = clone_repository(repo_url, github_token=token)
except Exception as e:
    if "SSL certificate" in str(e):
        # Handle SSL issues
        pass
    elif "authentication failed" in str(e):
        # Handle auth issues
        pass
    else:
        # Handle other errors
        pass
```

## Troubleshooting

### Common Issues

#### 1. **SSL Certificate Problems**
**Symptoms:** SSL certificate verification failed errors
**Solution:** Set `GITHUB_ENTERPRISE_DISABLE_SSL=true` or provide a CA bundle

#### 2. **Authentication Failures**
**Symptoms:** Authentication failed or 401 errors
**Solution:** Check your GitHub token and repository permissions

#### 3. **Network Timeouts**
**Symptoms:** Connection timeout or slow downloads
**Solution:** Check network connectivity and firewall settings

#### 4. **Repository Not Found**
**Symptoms:** 404 errors or repository not found messages
**Solution:** Verify repository URL and access permissions

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- Repository detection logic
- Method selection decisions
- SSL configuration details
- Network request details

## Migration from Old Implementation

The new Git operations utility replaces the basic Git cloning in `crawl_github_files.py`. Key improvements:

1. **Enterprise Support**: Automatic detection and configuration
2. **Better Error Handling**: Specific error messages and retry logic
3. **Resource Management**: Automatic cleanup and memory efficiency
4. **Method Selection**: Smart choice between Git clone and API download

The old implementation has been completely replaced, and all existing functionality is preserved with enhanced capabilities. 