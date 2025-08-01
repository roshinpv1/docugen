"""
HTML Generator Utility

Converts Markdown content to HTML with proper styling and structure.
"""

import re
import os
from typing import List, Dict, Any

def markdown_to_html(markdown_content: str) -> str:
    """
    Convert Markdown content to HTML with basic styling.
    
    Args:
        markdown_content: Raw markdown content
        
    Returns:
        HTML content with embedded CSS styling
    """
    
    # CSS styles for the documentation
    css_styles = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fafafa;
        }
        
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
            margin-top: 40px;
            margin-bottom: 20px;
        }
        
        h3 {
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        
        h4, h5, h6 {
            color: #34495e;
            margin-top: 25px;
            margin-bottom: 10px;
        }
        
        p {
            margin-bottom: 16px;
        }
        
        ul, ol {
            margin-bottom: 16px;
            padding-left: 20px;
        }
        
        li {
            margin-bottom: 8px;
        }
        
        code {
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }
        
        pre {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 20px 0;
        }
        
        pre code {
            background: none;
            color: inherit;
            padding: 0;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #7f8c8d;
            font-style: italic;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .mermaid {
            background: white;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
            text-align: center;
        }
        
        .highlight {
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }
        
        .warning {
            background-color: #f8d7da;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #dc3545;
            margin: 20px 0;
        }
        
        .info {
            background-color: #d1ecf1;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #17a2b8;
            margin: 20px 0;
        }
        
        .success {
            background-color: #d4edda;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #28a745;
            margin: 20px 0;
        }
        
        .toc {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc li {
            margin-bottom: 5px;
        }
        
        .toc a {
            color: #495057;
        }
        
        .toc a:hover {
            color: #3498db;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .container {
                padding: 20px;
            }
            
            pre {
                padding: 15px;
                font-size: 0.9em;
            }
        }
    </style>
    """
    
    # JavaScript for Mermaid diagrams
    mermaid_script = """
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true
            }
        });
    </script>
    """
    
    # Convert markdown to HTML
    html_content = markdown_content
    
    # Headers
    html_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    
    # Bold and italic
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
    html_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_content)
    
    # Mermaid diagrams (handle before code blocks)
    html_content = re.sub(r'```mermaid\n(.*?)\n```', r'<div class="mermaid">\1</div>', html_content, flags=re.DOTALL)
    
    # Alternative approach: handle code blocks line by line
    lines = html_content.split('\n')
    result_lines = []
    in_code_block = False
    code_language = 'text'
    code_content = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check for code block start
        if stripped.startswith('```'):
            if not in_code_block:
                # Start of code block
                in_code_block = True
                # Extract language if present
                lang_match = re.match(r'```(\w+)', stripped)
                code_language = lang_match.group(1) if lang_match else 'text'
                code_content = []
            else:
                # End of code block
                in_code_block = False
                # Create the code block HTML
                code_html = f'<pre><code class="language-{code_language}">{"\\n".join(code_content)}</code></pre>'
                result_lines.append(code_html)
        elif in_code_block:
            # Inside code block - collect content
            code_content.append(line)
        else:
            # Regular line - add to result
            result_lines.append(line)
    
    html_content = '\n'.join(result_lines)
    
    # Fix the language class if no language was specified
    html_content = re.sub(r'class="language-"', 'class="language-text"', html_content)
    
    # Inline code (handle after code blocks to avoid conflicts)
    html_content = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_content)
    
    # Links
    html_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_content)
    
    # Lists - handle unordered lists first
    lines = html_content.split('\n')
    result_lines = []
    in_ul = False
    in_ol = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check for unordered list items
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_ul:
                result_lines.append('<ul>')
                in_ul = True
            content = stripped[2:]  # Remove the bullet
            result_lines.append(f'<li>{content}</li>')
        # Check for ordered list items
        elif re.match(r'^\d+\. ', stripped):
            if not in_ol:
                result_lines.append('<ol>')
                in_ol = True
            content = re.sub(r'^\d+\. ', '', stripped)  # Remove the number
            result_lines.append(f'<li>{content}</li>')
        else:
            # Close any open lists
            if in_ul:
                result_lines.append('</ul>')
                in_ul = False
            if in_ol:
                result_lines.append('</ol>')
                in_ol = False
            result_lines.append(line)
    
    # Close any remaining open lists
    if in_ul:
        result_lines.append('</ul>')
    if in_ol:
        result_lines.append('</ol>')
    
    html_content = '\n'.join(result_lines)
    
    # Blockquotes
    html_content = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', html_content, flags=re.MULTILINE)
    
    # Horizontal rules
    html_content = re.sub(r'^---$', r'<hr>', html_content, flags=re.MULTILINE)
    
    # Paragraphs (only for lines that aren't already HTML tags)
    lines = html_content.split('\n')
    result_lines = []
    current_paragraph = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Empty line - end current paragraph
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
        elif stripped.startswith('<') and stripped.endswith('>'):
            # HTML tag - end current paragraph and add the tag
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            result_lines.append(line)
        elif stripped.startswith('<pre>') or stripped.startswith('<code>') or stripped.startswith('<ul>') or stripped.startswith('<ol>') or stripped.startswith('<li>') or stripped.startswith('<h1>') or stripped.startswith('<h2>') or stripped.startswith('<h3>') or stripped.startswith('<blockquote>') or stripped.startswith('<hr>') or stripped.startswith('<div class="mermaid">'):
            # HTML block elements - end current paragraph and add the tag
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            result_lines.append(line)
        else:
            # Regular text - add to current paragraph
            current_paragraph.append(stripped)
    
    # Handle any remaining paragraph content
    if current_paragraph:
        result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
    
    html_content = '\n'.join(result_lines)
    
    # Create the full HTML document
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Technical Documentation</title>
    {css_styles}
    {mermaid_script}
</head>
<body>
    <div class="container">
        {html_content}
    </div>
</body>
</html>"""
    
    return full_html

def generate_html_index(project_name: str, summary: str, repo_url: str, mermaid_diagram: str, chapter_links: List[Dict[str, str]]) -> str:
    """
    Generate HTML index page for technical documentation.
    
    Args:
        project_name: Name of the project
        summary: Project summary
        repo_url: Source repository URL
        mermaid_diagram: Mermaid diagram code
        chapter_links: List of chapter links with filename and title
        
    Returns:
        HTML content for the index page
    """
    
    # Generate chapter links HTML
    chapter_links_html = ""
    for i, chapter in enumerate(chapter_links, 1):
        chapter_links_html += f'<li><a href="{chapter["filename"]}">{i}. {chapter["title"]}</a></li>\n'
    
    # Convert markdown summary to HTML
    summary_html = markdown_to_html(summary)
    
    # Extract just the body content from the summary
    summary_body = re.search(r'<div class="container">(.*?)</div>', summary_html, re.DOTALL)
    summary_content = summary_body.group(1) if summary_body else summary
    
    index_content = f"""# Technical Documentation: {project_name}

{summary_content}

**Source Repository:** [{repo_url}]({repo_url})

## Architecture Overview

The following diagram shows the technical relationships between components:

```mermaid
{mermaid_diagram}
```

## Technical Components

{chr(10).join([f"{i}. [{chapter['title']}]({chapter['filename']})" for i, chapter in enumerate(chapter_links, 1)])}

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)
"""
    
    return markdown_to_html(index_content)

def convert_markdown_files_to_html(output_dir: str, project_name: str) -> None:
    """
    Convert all markdown files in the output directory to HTML.
    
    Args:
        output_dir: Directory containing markdown files
        project_name: Name of the project
    """
    
    # Create HTML directory
    html_dir = os.path.join(output_dir, "html")
    os.makedirs(html_dir, exist_ok=True)
    
    # Convert each markdown file to HTML
    for filename in os.listdir(output_dir):
        if filename.endswith('.md'):
            md_path = os.path.join(output_dir, filename)
            html_filename = filename.replace('.md', '.html')
            html_path = os.path.join(html_dir, html_filename)
            
            with open(md_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            html_content = markdown_to_html(markdown_content)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"  - Converted {filename} to {html_filename}")
    
    print(f"HTML documentation generated in: {html_dir}") 