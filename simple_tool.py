#!/usr/bin/env python3
"""
Simple Tool classes for ToolAgent.
"""

import json
import os
from typing import Dict, Any

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not found. Install with: pip install openai")
    exit(1)


class SimpleTool:
    """Base class for simple tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        raise NotImplementedError
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": {}, "required": []}
            }
        }


class FileReaderTool(SimpleTool):
    """Simple file reading tool."""
    
    def __init__(self):
        super().__init__(
            "file_reader", 
            "Read content from a text file"
        )
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        path = arguments.get("path", "")
        max_lines = int(arguments.get("max_lines", 100))
        
        if not path:
            return "Error: No file path provided"
        
        try:
            # Security check - only allow current directory and subdirectories
            abs_path = os.path.abspath(path)
            cwd = os.path.abspath(os.getcwd())
            if not abs_path.startswith(cwd):
                return f"Error: Access denied - path outside current directory"
            
            if not os.path.exists(path):
                return f"Error: File '{path}' not found"
            
            if not os.path.isfile(path):
                return f"Error: '{path}' is not a file"
            
            # Check if it's a text file
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line.rstrip())
                    
                    content = '\n'.join(lines)
                    total_lines = i + 1  # Total lines in file
                    
                    result = f"📄 File: {path}\n"
                    result += f"📊 Lines read: {len(lines)}/{total_lines}\n"
                    if total_lines > max_lines:
                        result += f"⚠️  Output limited to {max_lines} lines\n"
                    result += f"{'='*50}\n"
                    result += content
                    
                    return result
                    
            except UnicodeDecodeError:
                return f"Error: '{path}' appears to be a binary file"
                
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "Maximum number of lines to read (default: 100)",
                            "default": 100
                        }
                    },
                    "required": ["path"]
                }
            }
        }


class WebSearchTool(SimpleTool):
    """Web search tool using duckduckgo-search (ddgs)."""
    
    def __init__(self):
        super().__init__(
            "web_search",
            "Search the web using DuckDuckGo search engine"
        )
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        query = arguments.get("query", "")
        max_results = int(arguments.get("max_results", 5))
        
        if not query:
            return "Error: No search query provided"
        
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                return "Error: ddgs package not installed. Install with: pip install ddgs"
            
            with DDGS() as ddgs:
                # Perform text search
                results = list(ddgs.text(query, max_results=max_results))
            
            # Format results
            result = f"🔍 Web Search: '{query}'\n"
            result += f"{'='*50}\n"
            
            if results:
                for i, item in enumerate(results, 1):
                    title = item.get('title', 'No title')
                    url = item.get('href', 'No URL')
                    snippet = item.get('body', 'No description')
                    
                    result += f"  {i}. {title}\n"
                    result += f"     {url}\n"
                    result += f"     {snippet}\n\n"
            else:
                result += "No results found. Try a different search term.\n"
            
            return result
            
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find web pages"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to show (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }


class WebFetchTool(SimpleTool):
    """Web fetch tool for retrieving content from URLs."""
    
    def __init__(self):
        super().__init__(
            "web_fetch",
            "Fetch and extract text content from a web page URL"
        )
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        url = arguments.get("url", "")
        max_length = int(arguments.get("max_length", 5000))
        
        if not url:
            return "Error: No URL provided"
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            return "Error: URL must start with http:// or https://"
        
        try:
            # Try to import required libraries
            try:
                import requests
                from bs4 import BeautifulSoup
            except ImportError as e:
                missing_lib = str(e).split("'")[1]
                return f"Error: {missing_lib} package not installed. Install with: pip install {missing_lib}"
            
            # Fetch the webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text from common content areas
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.entry-content', '.article-body', '#content'
            ]
            
            main_content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    main_content = element.get_text(separator=' ', strip=True)
                    break
            
            # Fallback to body if no main content found
            if not main_content:
                main_content = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in main_content.split('\n') if line.strip()]
            content = '\n'.join(lines)
            
            # Limit content length
            if len(content) > max_length:
                content = content[:max_length] + "...[content truncated]"
            
            # Format result
            result = f"🌐 Web Fetch: {url}\n"
            result += f"{'='*50}\n"
            result += f"📄 Content ({len(content)} characters):\n\n"
            result += content
            
            return result
            
        except requests.exceptions.RequestException as e:
            return f"Error fetching URL: {str(e)}"
        except Exception as e:
            return f"Error processing web page: {str(e)}"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL of the web page to fetch content from"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum number of characters to return (default: 5000)",
                            "default": 5000
                        }
                    },
                    "required": ["url"]
                }
            }
        }


class CalculatorTool(SimpleTool):
    """Simple calculator tool."""
    
    def __init__(self):
        super().__init__(
            "calculator",
            "Perform mathematical calculations"
        )
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        expression = arguments.get("expression", "")
        
        if not expression:
            return "Error: No mathematical expression provided"
        
        try:
            # Security: Only allow safe mathematical operations
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"
            
            # Evaluate the expression safely
            result = eval(expression)
            
            return f"🧮 Calculator: {expression} = {result}"
            
        except Exception as e:
            return f"Error calculating: {str(e)}"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to calculate (e.g., '2 + 3 * 4')"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
