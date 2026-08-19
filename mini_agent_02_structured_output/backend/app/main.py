from fastapi import FastAPI

from app.routers.agent_router import agent_router
from app.routers.media_router import media_router


app = FastAPI(
    title="Mini Agent 02 · Prompt와 Structured Output",
    openapi_tags=[
        {
            "name": "01. LLM",
            "description": "mini_agent_01_llm에서 이어지는 기본 LLM 및 멀티모달 API",
        },
        {
            "name": "02. Prompt & Structured Output",
            "description": "Prompt 조립, Pydantic 검증, Structured Output API",
        },
    ],
)
app.include_router(agent_router)
app.include_router(media_router)
