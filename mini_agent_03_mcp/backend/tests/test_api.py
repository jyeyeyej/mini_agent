from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas import McpRunResult


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "stage": "mini_agent_03_mcp",
        "mcp_servers": {
            "travel": "streamable-http",
            "policy": "stdio",
        },
    }


def test_mcp_status_reports_discovered_tools(monkeypatch) -> None:
    async def fake_discover_tools() -> list[dict]:
        return [
            {"server": "travel", "name": "search_hotels"},
            {"server": "policy", "name": "get_hotel_policy"},
        ]

    monkeypatch.setattr(
        "backend.app.main.discover_tools",
        fake_discover_tools,
    )

    response = client.get("/api/mcp/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "connected"
    assert body["tool_count"] == 2
    assert {server["name"] for server in body["servers"]} == {
        "travel",
        "policy",
    }


def test_mcp_status_returns_503_when_discovery_fails(monkeypatch) -> None:
    async def fail_discovery() -> list[dict]:
        raise RuntimeError("test connection failure")

    monkeypatch.setattr(
        "backend.app.main.discover_tools",
        fail_discovery,
    )

    response = client.get("/api/mcp/status")

    assert response.status_code == 503
    assert "MCP Server 연결 실패" in response.json()["detail"]


def test_list_mcp_tools(monkeypatch) -> None:
    expected = [{
        "server": "travel",
        "name": "search_hotels",
        "public_name": "travel__search_hotels",
        "description": "호텔을 검색합니다.",
        "input_schema": {"type": "object"},
    }]

    async def fake_discover_tools() -> list[dict]:
        return expected

    monkeypatch.setattr(
        "backend.app.main.discover_tools",
        fake_discover_tools,
    )

    response = client.get("/api/mcp/tools")

    assert response.status_code == 200
    assert response.json() == {"tools": expected}


def test_list_mcp_resources(monkeypatch) -> None:
    expected = [{
        "server": "travel",
        "name": "baggage-policy",
        "uri": "travel://policy/baggage",
        "description": "수하물 정책",
    }]

    async def fake_discover_resources() -> list[dict]:
        return expected

    monkeypatch.setattr(
        "backend.app.main.discover_resources",
        fake_discover_resources,
    )

    response = client.get("/api/mcp/resources")

    assert response.status_code == 200
    assert response.json() == {"resources": expected}


def test_baggage_policy(monkeypatch) -> None:
    async def fake_read_resource(server_name: str, uri: str) -> str:
        assert server_name == "travel"
        assert uri == "travel://policy/baggage"
        return "기내 수하물은 10kg까지 허용됩니다."

    monkeypatch.setattr(
        "backend.app.main.read_resource",
        fake_read_resource,
    )

    response = client.get("/api/mcp/baggage-policy")

    assert response.status_code == 200
    assert response.json() == {
        "uri": "travel://policy/baggage",
        "content": "기내 수하물은 10kg까지 허용됩니다.",
    }


def test_run_mcp_agent(monkeypatch) -> None:
    async def fake_run_agent(question: str) -> McpRunResult:
        return McpRunResult(
            question=question,
            model="test-model",
            available_tools=["travel__search_hotels"],
            llm_calls=1,
            trace=[],
            answer="테스트 답변입니다.",
        )

    monkeypatch.setattr(
        "backend.app.main.run_agent",
        fake_run_agent,
    )

    response = client.post(
        "/api/mcp/run",
        json={"question": "서울 호텔을 찾아 주세요."},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "테스트 답변입니다."
    assert response.json()["llm_calls"] == 1


def test_run_mcp_agent_requires_non_empty_question() -> None:
    response = client.post("/api/mcp/run", json={"question": ""})

    assert response.status_code == 422


def test_run_mcp_agent_returns_400_for_value_error(monkeypatch) -> None:
    async def fail_run_agent(question: str) -> McpRunResult:
        raise ValueError("OPENAI_API_KEY가 필요합니다.")

    monkeypatch.setattr(
        "backend.app.main.run_agent",
        fail_run_agent,
    )

    response = client.post(
        "/api/mcp/run",
        json={"question": "서울 호텔을 찾아 주세요."},
    )

    assert response.status_code == 400
    assert "OPENAI_API_KEY" in response.json()["detail"]
