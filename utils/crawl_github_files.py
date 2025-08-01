import requests
import base64
import os
import tempfile
import git
import time
import fnmatch
from typing import Union, Set, List, Dict, Tuple, Any
from urllib.parse import urlparse
from .git_operations import clone_repository, cleanup_repository, get_repository_info

def crawl_github_files(
    repo_url, 
    token=None, 
    branch="main",  # Add branch parameter
    max_file_size: int = 1 * 1024 * 1024,  # 1 MB
    use_relative_paths: bool = False,
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None
):
    """
    Crawl files from a specific path in a GitHub repository at a specific commit.

    Args:
        repo_url (str): URL of the GitHub repository with specific path and commit
                        (e.g., 'https://github.com/microsoft/autogen/tree/e45a15766746d95f8cfaaa705b0371267bec812e/python/packages/autogen-core/src/autogen_core')
        token (str, optional): **GitHub personal access token.**
            - **Required for private repositories.**
            - **Recommended for public repos to avoid rate limits.**
            - Can be passed explicitly or set via the `GITHUB_TOKEN` environment variable.
        branch (str, optional): Git branch to clone (default: "main").
        max_file_size (int, optional): Maximum file size in bytes to download (default: 1 MB)
        use_relative_paths (bool, optional): If True, file paths will be relative to the specified subdirectory
        include_patterns (str or set of str, optional): Pattern or set of patterns specifying which files to include (e.g., "*.py", {"*.md", "*.txt"}).
                                                       If None, all files are included.
        exclude_patterns (str or set of str, optional): Pattern or set of patterns specifying which files to exclude.
                                                       If None, no files are excluded.

    Returns:
        dict: Dictionary with files and statistics
    """
    # Convert single pattern to set
    if include_patterns and isinstance(include_patterns, str):
        include_patterns = {include_patterns}
    if exclude_patterns and isinstance(exclude_patterns, str):
        exclude_patterns = {exclude_patterns}

    def should_include_file(file_path: str, file_name: str) -> bool:
        """Determine if a file should be included based on patterns"""
        # If no include patterns are specified, include all files
        if not include_patterns:
            include_file = True
        else:
            # Check if file matches any include pattern
            include_file = any(fnmatch.fnmatch(file_name, pattern) for pattern in include_patterns)

        # If exclude patterns are specified, check if file should be excluded
        if exclude_patterns and include_file:
            # Exclude if file matches any exclude pattern
            exclude_file = any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns)
            return not exclude_file

        return include_file

    # Parse GitHub URL to extract owner, repo, commit/branch, and path
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')
    
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    
    # Extract the basic components
    owner = path_parts[0]
    repo = path_parts[1]
    
    # Setup for GitHub API
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    def fetch_branches(owner: str, repo: str):
        """Get branches of the repository"""

        url = f"https://api.github.com/repos/{owner}/{repo}/branches"
        response = requests.get(url, headers=headers, timeout=(30, 30))

        if response.status_code == 404:
            if not token:
                print(f"Error 404: Repository not found or is private.\n"
                      f"If this is a private repository, please provide a valid GitHub token via the 'token' argument or set the GITHUB_TOKEN environment variable.")
            else:
                print(f"Error 404: Repository not found or insufficient permissions with the provided token.\n"
                      f"Please verify the repository exists and the token has access to this repository.")
            return []
            
        if response.status_code != 200:
            print(f"Error fetching the branches of {owner}/{repo}: {response.status_code} - {response.text}")
            return []

        return response.json()

    def check_tree(owner: str, repo: str, tree: str):
        """Check the repository has the given tree"""

        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree}"
        response = requests.get(url, headers=headers, timeout=(30, 30))

        return True if response.status_code == 200 else False 

    # Check if URL contains a specific branch/commit
    if len(path_parts) > 2 and 'tree' == path_parts[2]:
        join_parts = lambda i: '/'.join(path_parts[i:])

        branches = fetch_branches(owner, repo)
        branch_names = map(lambda branch: branch.get("name"), branches)

        # Fetching branches is not successfully
        if len(branches) == 0:
            return

        # To check branch name
        relevant_path = join_parts(3)

        # Find a match with relevant path and get the branch name
        filter_gen = (name for name in branch_names if relevant_path.startswith(name))
        ref = next(filter_gen, None)

        # If match is not found, check for is it a tree
        if ref == None:
            tree = path_parts[3]
            ref = tree if check_tree(owner, repo, tree) else None

        # If it is neither a tree nor a branch name
        if ref == None:
            print(f"The given path does not match with any branch and any tree in the repository.\n"
                  f"Please verify the path is exists.")
            return

        # Extract the subdirectory path
        if relevant_path.startswith(ref):
            subdir = relevant_path[len(ref):].lstrip('/')
        else:
            subdir = ""

        # Use the new git operations utility to clone the repository
        try:
            # Clone the repository using the new utility
            # Use the specified branch parameter if provided, otherwise use the ref from URL
            clone_branch = branch if branch != "main" else ref
            repo_path = clone_repository(repo_url, branch=clone_branch, github_token=token)
            
            # Get repository info for debugging
            repo_info = get_repository_info(repo_path)
            print(f"📊 Repository info: {repo_info}")
            
            # Walk directory and collect files
            files = {}
            skipped_files = []
            
            # Determine the base path for file collection
            base_path = repo_path
            if subdir and use_relative_paths:
                base_path = os.path.join(repo_path, subdir)
                if not os.path.exists(base_path):
                    print(f"⚠️ Subdirectory {subdir} not found in repository")
                    cleanup_repository(repo_path)
                    return {"files": {}, "stats": {"error": f"Subdirectory {subdir} not found"}}

            for root, dirs, filenames in os.walk(base_path):
                for filename in filenames:
                    abs_path = os.path.join(root, filename)
                    
                    # Calculate relative path from the base path
                    if use_relative_paths:
                        rel_path = os.path.relpath(abs_path, base_path)
                    else:
                        rel_path = os.path.relpath(abs_path, repo_path)

                    # Check file size
                    try:
                        file_size = os.path.getsize(abs_path)
                    except OSError:
                        continue

                    if file_size > max_file_size:
                        skipped_files.append((rel_path, file_size))
                        print(f"Skipping {rel_path}: size {file_size} exceeds limit {max_file_size}")
                        continue

                    # Check include/exclude patterns
                    if not should_include_file(rel_path, filename):
                        print(f"Skipping {rel_path}: does not match include/exclude patterns")
                        continue

                    # Read content
                    try:
                        with open(abs_path, "r", encoding="utf-8-sig") as f:
                            content = f.read()
                        files[rel_path] = content
                        print(f"Added {rel_path} ({file_size} bytes)")
                    except Exception as e:
                        print(f"Failed to read {rel_path}: {e}")

            # Clean up the cloned repository
            cleanup_repository(repo_path)

            return {
                "files": files,
                "stats": {
                    "downloaded_count": len(files),
                    "skipped_count": len(skipped_files),
                    "skipped_files": skipped_files,
                    "base_path": subdir if use_relative_paths else None,
                    "include_patterns": include_patterns,
                    "exclude_patterns": exclude_patterns,
                    "source": "git_clone",
                    "branch": clone_branch
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to clone repository: {e}")
            return {"files": {}, "stats": {"error": str(e)}}

    else:
        # No specific branch/commit specified, use the specified branch parameter
        print(f"No specific branch/commit specified in URL, using specified branch: {branch}")
        
        # Use the new git operations utility to clone the repository
        try:
            # Clone the repository using the new utility with the specified branch
            repo_path = clone_repository(repo_url, branch=branch, github_token=token)
            
            # Get repository info for debugging
            repo_info = get_repository_info(repo_path)
            print(f"📊 Repository info: {repo_info}")
            
            # Walk directory and collect files
            files = {}
            skipped_files = []

            for root, dirs, filenames in os.walk(repo_path):
                for filename in filenames:
                    abs_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(abs_path, repo_path)

                    # Check file size
                    try:
                        file_size = os.path.getsize(abs_path)
                    except OSError:
                        continue

                    if file_size > max_file_size:
                        skipped_files.append((rel_path, file_size))
                        print(f"Skipping {rel_path}: size {file_size} exceeds limit {max_file_size}")
                        continue

                    # Check include/exclude patterns
                    if not should_include_file(rel_path, filename):
                        print(f"Skipping {rel_path}: does not match include/exclude patterns")
                        continue

                    # Read content
                    try:
                        with open(abs_path, "r", encoding="utf-8-sig") as f:
                            content = f.read()
                        files[rel_path] = content
                        print(f"Added {rel_path} ({file_size} bytes)")
                    except Exception as e:
                        print(f"Failed to read {rel_path}: {e}")

            # Clean up the cloned repository
            cleanup_repository(repo_path)

            return {
                "files": files,
                "stats": {
                    "downloaded_count": len(files),
                    "skipped_count": len(skipped_files),
                    "skipped_files": skipped_files,
                    "base_path": None,
                    "include_patterns": include_patterns,
                    "exclude_patterns": exclude_patterns,
                    "source": "git_clone",
                    "branch": branch
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to clone repository: {e}")
            return {"files": {}, "stats": {"error": str(e)}}


if __name__ == "__main__":
    # Test the updated crawl_github_files function
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Warning: No GitHub token found in environment variable 'GITHUB_TOKEN'.\n"
              "This may cause rate limiting for public repositories.\n"
              "For private repositories, a token is required.")
    
    # Test with a public repository
    repo_url = "https://github.com/pydantic/pydantic/tree/6c38dc93f40a47f4d1350adca9ec0d72502e223f/pydantic"
    
    print(f"Testing crawl_github_files with {repo_url}")
    result = crawl_github_files(
        repo_url=repo_url,
        token=github_token,
        branch="main",  # Add branch parameter
        max_file_size=100 * 1024,  # 100 KB
        include_patterns="*.py",
        exclude_patterns="tests/*"
    )
    
    print(f"Result: {result}")
    if result and "files" in result:
        print(f"Downloaded {len(result['files'])} files")
        for filename in list(result['files'].keys())[:5]:  # Show first 5 files
            print(f"  - {filename}")
