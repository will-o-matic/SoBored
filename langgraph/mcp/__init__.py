"""
MCP (Model Context Protocol) integration for SoBored event aggregator.
"""

from .mcp_client import (
    MCPClientWrapper,
    create_mcp_client,
    get_default_mcp_servers,
    initialize_mcp_for_agent
)

__all__ = [
    "MCPClientWrapper",
    "create_mcp_client", 
    "get_default_mcp_servers",
    "initialize_mcp_for_agent"
]