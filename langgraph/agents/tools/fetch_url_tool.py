import re
from langchain_core.tools import tool

@tool
def fetch_url_content(url: str) -> dict:
    """
    Fetch webpage content from URL and extract meaningful text.
    
    Args:
        url: URL to fetch content from
        
    Returns:
        Dict containing webpage content, title, and fetch status
    """
    try:
        print(f"[FETCH] URL: {url}")
        if not url or not re.match(r'https?://', url):
            print(f"[FETCH] Invalid URL format")
            return {
                "fetch_status": "failed",
                "fetch_error": "Invalid or missing URL"
            }
        
        # Try to use MCP fetch tool from Claude Code environment
        try:
            # Check if we have access to mcp__fetch__fetch tool
            import sys
            if 'mcp__fetch__fetch' in globals() or 'mcp__fetch__fetch' in dir():
                # MCP fetch tool is available
                mcp_fetch = globals().get('mcp__fetch__fetch') or getattr(sys.modules.get('__main__', sys.modules[__name__]), 'mcp__fetch__fetch', None)
                if mcp_fetch:
                    print(f"[FETCH] Using MCP fetch tool")
                    result = mcp_fetch(url=url, max_length=5000)
                    
                    # Extract title from the fetched content
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', result, re.IGNORECASE)
                    webpage_title = title_match.group(1).strip() if title_match else "Untitled"
                    
                    result_data = {
                        "webpage_content": result,
                        "webpage_title": webpage_title,
                        "fetch_status": "success"
                    }
                    print(f"[FETCH] MCP Success - Title: {webpage_title}")
                    return result_data
            
            # Try checking if Claude Code tools are available via different methods
            try:
                # Try direct import approach
                from claude_code import fetch_url
                print(f"[FETCH] Using claude_code.fetch_url")
                result = fetch_url(url, max_length=5000)
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', result, re.IGNORECASE)
                webpage_title = title_match.group(1).strip() if title_match else "Untitled"
                return {
                    "webpage_content": result,
                    "webpage_title": webpage_title,
                    "fetch_status": "success"
                }
            except ImportError:
                pass
            
            # For now, fall back to requests since MCP isn't properly integrated
            print(f"[FETCH] MCP not available, using requests fallback")
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, timeout=10, headers=headers)
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
            
            result_data = {
                "webpage_content": webpage_content,
                "webpage_title": webpage_title,
                "fetch_status": "success"
            }
            print(f"[FETCH] Requests Success - Title: {webpage_title}, Content length: {len(webpage_content)}")
            return result_data
                
        except Exception as e:
            print(f"[FETCH] All methods failed: {e}")
            return {
                "fetch_status": "failed",
                "fetch_error": f"Unable to fetch URL: {str(e)}. Website may require JavaScript or specific browser features."
            }
        
    except Exception as e:
        return {
            "fetch_status": "failed",
            "fetch_error": f"URL fetch failed: {str(e)}"
        }