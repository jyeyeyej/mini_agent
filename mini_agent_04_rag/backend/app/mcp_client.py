"""외부 Streamable HTTP MCP 서버와 통신하는 공통 클라이언트."""

from __future__ import annotations

from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.core.config import settings


async def list_tools(server_url: str) -> list[dict[str, Any]]:
    """MCP 서버가 제공하는 도구 목록을 반환합니다."""
    async with streamablehttp_client(server_url) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            return [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                }
                for tool in tools
            ]


async def call_tool(
    server_url: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """지정한 MCP 서버의 도구를 호출합니다."""
    async with streamablehttp_client(server_url) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(tool_name, arguments or {})
            return [
                content.model_dump()
                for content in result.content
            ]


async def list_labs_tools() -> list[dict[str, Any]]:
    """10_labs MCP 서버의 도구 목록."""
    return await list_tools(settings.labs_mcp_url)


async def call_labs_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """10_labs MCP 서버의 도구 호출."""
    return await call_tool(settings.labs_mcp_url, tool_name, arguments)


async def list_tour_tools() -> list[dict[str, Any]]:
    """tour MCP 서버의 도구 목록."""
    return await list_tools(settings.tour_mcp_url)


async def call_tour_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """tour MCP 서버의 도구 호출."""
    return await call_tool(settings.tour_mcp_url, tool_name, arguments)