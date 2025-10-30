#!/usr/bin/env python3
"""
Simple Tool Validation Script
============================

Lightweight validation for tool-agent tools to quickly identify issues.
"""

import sys
import os
import tempfile
from typing import Dict, Tuple, Any

# Note: Using importlib to handle the hyphenated filename
import importlib.util
import importlib

spec = importlib.util.spec_from_file_location("tool_agent", "tool-agent.py")
tool_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool_agent_module)

FileReaderTool = tool_agent_module.FileReaderTool
WebSearchTool = tool_agent_module.WebSearchTool
WebFetchTool = tool_agent_module.WebFetchTool
CalculatorTool = tool_agent_module.CalculatorTool


class ToolValidator:
    """Simple validator for tool-agent tools."""
    
    def __init__(self):
        self.tools = {
            "file_reader": FileReaderTool(),
            "web_search": WebSearchTool(),
            "web_fetch": WebFetchTool(),
            "calculator": CalculatorTool()
        }
        self.results = {}
    
    def validate_file_reader(self) -> Tuple[bool, str]:
        """Test file reader tool."""
        tool = self.tools["file_reader"]
        
        # Test 1: Read existing file (README.md should exist)
        try:
            result = tool.execute({"path": "README.md", "max_lines": 5})
            if "📄 File: README.md" in result and "Error:" not in result:
                return True, "Successfully read README.md"
            else:
                return False, f"Unexpected output: {result[:100]}..."
        except Exception as e:
            return False, f"Exception: {str(e)}"
        
        # Test 2: Error handling for non-existent file
        try:
            result = tool.execute({"path": "non_existent_file.txt"})
            if "Error:" in result and "not found" in result:
                return True, "Properly handles missing files"
            else:
                return False, "Should handle missing files with error"
        except Exception as e:
            return False, f"Exception in error test: {str(e)}"
    
    def validate_calculator(self) -> Tuple[bool, str]:
        """Test calculator tool."""
        tool = self.tools["calculator"]
        
        # Test 1: Basic arithmetic
        try:
            result = tool.execute({"expression": "2 + 3"})
            if "5" in result and "🧮" in result:
                return True, "Basic arithmetic works"
            else:
                return False, f"Unexpected output: {result}"
        except Exception as e:
            return False, f"Exception: {str(e)}"
        
        # Test 2: Error handling for invalid expression
        try:
            result = tool.execute({"expression": "invalid"})
            if "Error:" in result:
                return True, "Properly handles invalid expressions"
            else:
                return False, "Should handle invalid expressions with error"
        except Exception as e:
            return False, f"Exception in error test: {str(e)}"
    
    def validate_web_search(self) -> Tuple[bool, str]:
        """Test web search tool."""
        tool = self.tools["web_search"]
        
        # Test with a query that should work (programming topics work well)
        try:
            result = tool.execute({"query": "python programming language", "max_results": 2})
            
            # Check for actual success (has URLs, not just "no results")
            if "Error performing web search:" in result:
                # Extract the error for debugging
                error_msg = result.split("Error performing web search:")[1].strip()
                return False, f"Web search failed: {error_msg}"
            elif "No results found" in result:
                return False, "Web search returns 'No results found' for basic queries"
            elif "https://" in result or "http://" in result:
                return True, "Web search working and returning URLs"
            else:
                return False, f"Web search returned unexpected format: {result[:200]}..."
                
        except Exception as e:
            return False, f"Exception during web search: {str(e)}"
    
    def validate_web_fetch(self) -> Tuple[bool, str]:
        """Test web fetch tool."""
        tool = self.tools["web_fetch"]
        
        # Test with a simple, reliable URL
        try:
            result = tool.execute({"url": "https://example.com", "max_length": 1000})
            
            # Check for success indicators
            if "Error fetching URL:" in result or "Error processing web page:" in result:
                error_msg = result.split("Error:")[1].strip() if "Error:" in result else "Unknown error"
                return False, f"Web fetch failed: {error_msg}"
            elif "🌐 Web Fetch:" in result and "Content" in result:
                return True, "Web fetch working and extracting content"
            else:
                return False, f"Web fetch returned unexpected format: {result[:200]}..."
                
        except Exception as e:
            return False, f"Exception during web fetch: {str(e)}"
    
    def validate_schemas(self) -> Tuple[bool, str]:
        """Validate tool schemas are properly formatted."""
        try:
            for name, tool in self.tools.items():
                schema = tool.get_schema()
                
                # Basic schema validation
                required_keys = ["type", "function"]
                for key in required_keys:
                    if key not in schema:
                        return False, f"Tool {name}: Missing '{key}' in schema"
                
                func_keys = ["name", "description", "parameters"]
                for key in func_keys:
                    if key not in schema["function"]:
                        return False, f"Tool {name}: Missing '{key}' in function schema"
                
                # Check parameter structure
                params = schema["function"]["parameters"]
                if params.get("type") != "object":
                    return False, f"Tool {name}: Parameters should be type 'object'"
                
                if "properties" not in params:
                    return False, f"Tool {name}: Missing 'properties' in parameters"
                
                if "required" not in params:
                    return False, f"Tool {name}: Missing 'required' in parameters"
            
            return True, "All tool schemas valid"
            
        except Exception as e:
            return False, f"Schema validation exception: {str(e)}"
    
    def run_all_validations(self) -> Dict[str, Tuple[bool, str]]:
        """Run all validations and return results."""
        print("🔧 Running Tool Validations...")
        print("=" * 50)
        
        validations = {
            "file_reader": self.validate_file_reader,
            "calculator": self.validate_calculator, 
            "web_search": self.validate_web_search,
            "web_fetch": self.validate_web_fetch,
            "schemas": self.validate_schemas
        }
        
        results = {}
        
        for name, validator in validations.items():
            try:
                print(f"Testing {name}...", end=" ")
                success, message = validator()
                results[name] = (success, message)
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{status}")
                
            except Exception as e:
                results[name] = (False, f"Validation crashed: {str(e)}")
                print(f"💥 CRASH")
        
        return results
    
    def print_summary(self, results: Dict[str, Tuple[bool, str]]):
        """Print validation summary."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for success, _ in results.values() if success)
        total = len(results)
        
        for name, (success, message) in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {name}: {message}")
        
        print(f"\nOverall: {passed}/{total} validations passed")
        
        if passed == total:
            print("🎉 All tools are working correctly!")
        else:
            print("⚠️  Some tools need attention before running demos.")
        
        # Specific recommendations for common issues
        if "web_search" in results and not results["web_search"][0]:
            print("\n💡 Web Search Issues - Try:")
            print("   • Check internet connection")
            print("   • Verify DuckDuckGo API is accessible")
            print("   • Check for network/firewall restrictions")


def main():
    """Main entry point."""
    validator = ToolValidator()
    results = validator.run_all_validations()
    validator.print_summary(results)
    
    # Exit with error code if any validation failed
    failed = any(not success for success, _ in results.values())
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
