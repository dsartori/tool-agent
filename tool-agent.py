#!/usr/bin/env python3
"""
ToolAgent Demo - CLI for AI with Tool Chaining
========================================================

A minimal demonstration of AI tool chaining for Hackforge.
Features: OpenAI integration, tool calls, round management, stdin input.
"""

import json
import sys
import os
import subprocess
import argparse
from typing import Dict, List, Any, Optional
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not found. Install with: pip install openai")
    sys.exit(1)


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
            # Use ddgs (new name for duckduckgo-search) for more reliable search
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


class ToolAgent:
    """Main class for ToolAgent CLI."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.client = OpenAI(
            api_key=os.environ.get("LLM_API_KEY"),
            base_url=os.environ.get("LLM_BASE_URL")
        )
        
        # Initialize tools
        self.tools = {
            "file_reader": FileReaderTool(),
            "web_search": WebSearchTool(),
            "web_fetch": WebFetchTool(),
            "calculator": CalculatorTool()
        }
        
        # Round management
        self.max_rounds = self.config.get("max_rounds", 5)
        self.current_round = 0
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file '{config_path}' not found, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "model": "moonshotai/Kimi-K2-Instruct",
            "temperature": 0.7,
            "system_prompt": "You are a helpful AI assistant with access to tools. Use tools when helpful to provide accurate, current information.",
            "max_rounds": 5
        }
    
    def _show_progress(self, round_num: int, message: str):
        """Show progress indicator."""
        print(f"🔄 Round {round_num}/{self.max_rounds}: {message}")
    
    def _detect_tool_call_loop(self, tool_calls: List[Dict], history: List[List[Dict]]) -> bool:
        """Simple loop detection for repeated tool calls."""
        if len(history) < 2:
            return False
        
        # Check if the same tool call pattern is repeating
        recent_calls = history[-1] if history else []
        if not recent_calls:
            return False
        
        # Compare with the round before last
        if len(history) >= 3:
            earlier_calls = history[-3]
            if len(recent_calls) == len(earlier_calls):
                for i, call in enumerate(recent_calls):
                    if i < len(earlier_calls):
                        current_name = call.get("function", {}).get("name")
                        earlier_name = earlier_calls[i].get("function", {}).get("name")
                        if current_name != earlier_name:
                            return False
                return True
        
        return False
    
    def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results."""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            arguments_str = tool_call.get("function", {}).get("arguments", "{}")
            
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                arguments = {}
            
            if tool_name not in self.tools:
                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "name": tool_name,
                    "content": f"Error: Tool '{tool_name}' not found"
                })
                continue
            
            # Execute the tool
            tool = self.tools[tool_name]
            tool_result = tool.execute(arguments)
            
            print(f"  🛠️  {tool_name}: {arguments.get('path', arguments.get('query', arguments.get('expression', 'executing')))}")
            
            results.append({
                "tool_call_id": tool_call.get("id"),
                "name": tool_name,
                "content": tool_result
            })
        
        return results
    
    def chat(self, message: str) -> str:
        """Main chat function with tool chaining."""
        # Prepare messages
        messages = [
            {"role": "system", "content": self.config["system_prompt"]},
            {"role": "user", "content": message}
        ]
        
        tool_schemas = [tool.get_schema() for tool in self.tools.values()]
        tool_call_history = []
        
        for round_num in range(1, self.max_rounds + 1):
            self.current_round = round_num
            
            # Get response from OpenAI
            self._show_progress(round_num, "Thinking...")
            
            try:
                response = self.client.chat.completions.create(
                    model=self.config["model"],
                    messages=messages,
                    temperature=self.config["temperature"],
                    tools=tool_schemas,
                    tool_choice="auto"
                )
            except Exception as e:
                return f"Error calling OpenAI API: {str(e)}"
            
            choice = response.choices[0]
            message_obj = choice.message
            
            # Add assistant response to messages
            assistant_message = {
                "role": "assistant",
                "content": message_obj.content or ""
            }
            
            if hasattr(message_obj, 'tool_calls') and message_obj.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message_obj.tool_calls
                ]
                
                # Check for loops before executing
                if self._detect_tool_call_loop(assistant_message["tool_calls"], tool_call_history):
                    messages.append({
                        "role": "system",
                        "content": "Stop repeating the same tool calls. Provide a response based on the information you already have."
                    })
                    continue
                
                tool_call_history.append(assistant_message["tool_calls"])
                messages.append(assistant_message)
                
                # Execute tools
                self._show_progress(round_num, "Executing tools...")
                tool_results = self._execute_tool_calls(assistant_message["tool_calls"])
                
                # Add tool results to messages
                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "name": result["name"],
                        "content": result["content"]
                    })
                
                # Continue to next round
                continue
            else:
                # No tool calls, final response
                messages.append(assistant_message)
                print(f"✅ Complete!")
                return message_obj.content or "No response"
        
        # Max rounds reached
        return f"⚠️  Maximum rounds ({self.max_rounds}) reached. Here's what I found so far."
    
    def run_interactive(self):
        """Run interactive CLI mode."""
        print("🤖 ToolAgent Demo - AI with Tool Chaining")
        print("Type 'quit' to exit, 'help' for available tools")
        print(f"📊 Max rounds: {self.max_rounds}")
        print()
        
        while True:
            try:
                message = input("> ").strip()
                
                if message.lower() in ['quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                if message.lower() == 'help':
                    print("\n🛠️  Available Tools:")
                    for name, tool in self.tools.items():
                        print(f"  • {name}: {tool.description}")
                    print()
                    continue
                
                if message:
                    print()
                    response = self.chat(message)
                    print(f"\n{response}\n")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                break


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ToolAgent Demo - AI with Tool Chaining")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("message", nargs="?", help="Message to send (if not provided, enters interactive mode)")
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = ToolAgent(args.config)
    
    # Check if message provided via stdin
    if not sys.stdin.isatty():
        message = sys.stdin.read().strip()
        if message:
            response = demo.chat(message)
            print(response)
        else:
            print("Error: No input provided", file=sys.stderr)
            sys.exit(1)
    elif args.message:
        # Single message mode
        response = demo.chat(args.message)
        print(response)
    else:
        # Interactive mode
        demo.run_interactive()


if __name__ == "__main__":
    main()
