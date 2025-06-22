import re
from typing import Dict, Any
from utils.state import EventState

def fetch_url_content(state: EventState) -> Dict[str, Any]:
    """
    Fetch webpage content from URL and extract meaningful text.
    
    Args:
        state: Current EventState with classified URL
        
    Returns:
        Dict containing webpage content and fetch status
    """
    try:
        if state.input_type != "url" or not state.raw_input:
            return {"fetch_status": "skipped"}
        
        # Extract URL from raw input
        url_match = re.search(r'https?://\S+', state.raw_input)
        if not url_match:
            return {
                "fetch_status": "failed",
                "fetch_error": "No valid URL found in input"
            }
        
        url = url_match.group(0)
        
        # Try to use MCP fetch if available
        try:
            # In Claude Code environment, MCP tools may be available as globals
            if 'mcp__fetch__fetch' in globals():
                mcp_fetch = globals()['mcp__fetch__fetch']
                result = mcp_fetch(url=url, max_length=5000)
                
                # Extract title from the fetched content
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', result, re.IGNORECASE)
                webpage_title = title_match.group(1).strip() if title_match else "Untitled"
                
                return {
                    "webpage_content": result,
                    "webpage_title": webpage_title,
                    "fetch_status": "success"
                }
            else:
                raise ImportError("MCP fetch not available")
                
        except Exception:
            # Fallback: try to use requests or other library
            try:
                import requests
                from bs4 import BeautifulSoup
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                webpage_title = title_tag.get_text().strip() if title_tag else "Untitled"
                
                # Remove script, style, and other non-content elements
                for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    script.decompose()
                
                # Extract main content
                main_content = soup.find('main') or soup.find('article') or soup.find('body')
                if main_content:
                    webpage_content = main_content.get_text()
                else:
                    webpage_content = soup.get_text()
                
                # Clean up whitespace
                webpage_content = re.sub(r'\s+', ' ', webpage_content).strip()
                webpage_content = webpage_content[:5000]  # Limit content length
                
                return {
                    "webpage_content": webpage_content,
                    "webpage_title": webpage_title,
                    "fetch_status": "success"
                }
                
            except Exception as e:
                return {
                    "fetch_status": "failed",
                    "fetch_error": f"Fallback fetch failed: {str(e)}"
                }
        
    except Exception as e:
        return {
            "fetch_status": "failed",
            "fetch_error": f"URL fetch failed: {str(e)}"
        }