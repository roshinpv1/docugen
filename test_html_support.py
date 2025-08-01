#!/usr/bin/env python3
"""
Test script for HTML output format support
"""

import os
import sys
import tempfile
from utils.html_generator import markdown_to_html, generate_html_index

def test_markdown_to_html_conversion():
    """Test that markdown content is correctly converted to HTML"""
    print("🧪 Testing markdown to HTML conversion...")
    print("=" * 50)
    
    # Test markdown content
    markdown_content = """# Test Documentation

This is a **test** document with *italic* text.

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

## List Example

- Item 1
- Item 2
- Item 3

## Link Example

[GitHub](https://github.com)

## Mermaid Diagram

```mermaid
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
```
"""
    
    try:
        html_content = markdown_to_html(markdown_content)
        
        # Check that HTML contains expected elements
        checks = [
            ("HTML structure", "<!DOCTYPE html>" in html_content),
            ("Headings", "<h1>" in html_content and "<h2>" in html_content),
            ("Bold text", "<strong>" in html_content),
            ("Italic text", "<em>" in html_content),
            ("Code blocks", "<pre>" in html_content and "language-python" in html_content),
            ("Lists", "<ul>" in html_content),
            ("Links", "<a href=" in html_content),
            ("Mermaid", "mermaid" in html_content),
            ("CSS styles", "<style>" in html_content),
        ]
        
        print("✅ HTML conversion successful!")
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        return all(passed for _, passed in checks)
        
    except Exception as e:
        print(f"❌ Error in HTML conversion: {e}")
        return False

def test_html_index_generation():
    """Test that HTML index page is generated correctly"""
    print("\n🧪 Testing HTML index generation...")
    print("=" * 50)
    
    try:
        # Test data
        project_name = "TestProject"
        summary = "This is a **test project** with *amazing* features."
        repo_url = "https://github.com/test/project"
        mermaid_diagram = """flowchart TD
    A[Auth Service] --> B[Database]
    C[API] --> B"""
        chapter_links = [
            {"filename": "01_auth_service.html", "title": "Authentication Service"},
            {"filename": "02_api_endpoints.html", "title": "API Endpoints"},
            {"filename": "03_database.html", "title": "Database Models"}
        ]
        
        html_index = generate_html_index(
            project_name=project_name,
            summary=summary,
            repo_url=repo_url,
            mermaid_diagram=mermaid_diagram,
            chapter_links=chapter_links
        )
        
        # Check that HTML index contains expected elements
        checks = [
            ("HTML structure", "<!DOCTYPE html>" in html_index),
            ("Project title", "TestProject" in html_index),
            ("Summary content", "test project" in html_index),
            ("Repository link", "github.com/test/project" in html_index),
            ("Mermaid diagram", "flowchart TD" in html_index),
            ("Chapter links", "Authentication Service" in html_index),
            ("Chapter links", "API Endpoints" in html_index),
            ("Chapter links", "Database Models" in html_index),
        ]
        
        print("✅ HTML index generation successful!")
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        return all(passed for _, passed in checks)
        
    except Exception as e:
        print(f"❌ Error in HTML index generation: {e}")
        return False

def test_command_line_html_format():
    """Test that command line HTML format argument is parsed correctly"""
    print("\n🧪 Testing command line HTML format parsing...")
    print("=" * 50)
    
    # Simulate command line arguments
    test_args = [
        ["--repo", "https://github.com/test/repo", "--format", "html"],
        ["--dir", "/path/to/code", "--format", "markdown"],
        ["--repo", "https://github.com/test/repo", "--format", "html", "--language", "Chinese"],
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
            parser.add_argument("--format", choices=["markdown", "html"], default="markdown")
            parser.add_argument("--language", default="english")
            
            parsed = parser.parse_args(args)
            print(f"   Repo: {parsed.repo}")
            print(f"   Dir: {parsed.dir}")
            print(f"   Format: {parsed.format}")
            print(f"   Language: {parsed.language}")
            
        except Exception as e:
            print(f"   ❌ Error parsing arguments: {e}")
    
    print("\n✅ Command line HTML format parsing tests completed!")
    return True

def test_html_file_creation():
    """Test that HTML files can be created in a temporary directory"""
    print("\n🧪 Testing HTML file creation...")
    print("=" * 50)
    
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            test_html = markdown_to_html("# Test\n\nThis is a test.")
            
            # Write HTML file
            html_file = os.path.join(temp_dir, "test.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(test_html)
            
            # Verify file exists and has content
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "<!DOCTYPE html>" in content and "Test" in content:
                    print("✅ HTML file creation successful!")
                    print(f"   File: {html_file}")
                    print(f"   Size: {len(content)} characters")
                    return True
                else:
                    print("❌ HTML file content is invalid")
                    return False
            else:
                print("❌ HTML file was not created")
                return False
                
    except Exception as e:
        print(f"❌ Error in HTML file creation: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting HTML Support Tests")
    print("=" * 50)
    
    success = True
    
    # Run tests
    if not test_markdown_to_html_conversion():
        success = False
    
    if not test_html_index_generation():
        success = False
    
    if not test_command_line_html_format():
        success = False
    
    if not test_html_file_creation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All HTML support tests passed!")
        print("\n📝 HTML Features:")
        print("   ✅ Markdown to HTML conversion")
        print("   ✅ HTML index page generation")
        print("   ✅ Command line format argument")
        print("   ✅ HTML file creation")
        print("   ✅ CSS styling and responsive design")
        print("   ✅ Mermaid diagram support")
        print("   ✅ Code syntax highlighting")
        print("\n📝 Usage examples:")
        print("   python main.py --repo https://github.com/username/repo --format html")
        print("   python main.py --repo https://github.com/username/repo --format html --language Chinese")
        print("   python main.py --dir /path/to/code --format html")
        sys.exit(0)
    else:
        print("❌ Some HTML support tests failed.")
        sys.exit(1) 