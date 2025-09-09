
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import (
    ErrorResponse,
    FollowupRequest,
    FollowupResponse,
    GenerateRequest,
    GenerateResponse,
    UsageInfo,
)
from .services.llm_client import LLMClient
from .services.logger import generate_user_id, json_logger
from .services.parsers import parse_cards_from_text, parse_followup_from_text
from .services.prompts import build_cards_system_prompt, build_followup_system_prompt

app = FastAPI(title="EasyGPT Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm_client = LLMClient()


@app.get("/health")
async def healthz() -> dict[str, Any]:
    return {"status": "ok"}


@app.post("/v1/generate", response_model=GenerateResponse, responses={400: {"model": ErrorResponse}})
async def generate(payload: GenerateRequest):
    user_id = generate_user_id()
    start_time = time.time()
    
    try:
        system_prompt = build_cards_system_prompt(payload.system)
        
        # Log user request + system prompt
        json_logger.log_user_request(
            user_id=user_id,
            request_type="generate",
            prompt=payload.prompt,
            system_prompt=system_prompt,
            provider=(payload.provider and payload.provider.value) if payload.provider else None,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )

        text, usage = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=payload.prompt,
            provider=(payload.provider and payload.provider.value) if payload.provider else None,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
        
        # Log model response
        json_logger.log_model_response(
            user_id=user_id,
            request_type="generate",
            model_output=text,
            provider=usage.get("provider", ""),
            model=usage.get("model", ""),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            latency_ms=usage.get("latency_ms"),
        )
        
        cards, meta = parse_cards_from_text(text)
        usage_model = UsageInfo(
            provider=usage.get("provider", ""),
            model=usage.get("model", ""),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            latency_ms=usage.get("latency_ms"),
        )
        return GenerateResponse(cards=cards, usage=usage_model, raw_text=text, meta=meta)
    except Exception as exc:
        # Log error
        json_logger.log_error(
            user_id=user_id,
            request_type="generate",
            error_message=str(exc),
        )
        # Return structured error for the UI
        raise HTTPException(status_code=400, detail={
            "error_type": "generation_error",
            "message": str(exc),
        })


@app.post("/v1/followup", response_model=FollowupResponse, responses={400: {"model": ErrorResponse}})
async def followup(payload: FollowupRequest):
    user_id = generate_user_id()
    
    try:
        system_prompt = build_followup_system_prompt(
            current_card_title=payload.current_card_title,
            current_card_content=payload.current_card_content,
            user_system=None,
        )
        
        # Log user request + system prompt
        json_logger.log_user_request(
            user_id=user_id,
            request_type="followup",
            prompt=payload.question,
            system_prompt=system_prompt,
            provider=(payload.provider and payload.provider.value) if payload.provider else None,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )

        text, usage = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=payload.question,
            provider=(payload.provider and payload.provider.value) if payload.provider else None,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
        
        # Log model response
        json_logger.log_model_response(
            user_id=user_id,
            request_type="followup",
            model_output=text,
            provider=usage.get("provider", ""),
            model=usage.get("model", ""),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            latency_ms=usage.get("latency_ms"),
        )
        
        card = parse_followup_from_text(text)
        usage_model = UsageInfo(
            provider=usage.get("provider", ""),
            model=usage.get("model", ""),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            latency_ms=usage.get("latency_ms"),
        )
        return FollowupResponse(card=card, usage=usage_model, raw_text=text)
    except Exception as exc:
        # Log error
        json_logger.log_error(
            user_id=user_id,
            request_type="followup",
            error_message=str(exc),
        )
        raise HTTPException(status_code=400, detail={
            "error_type": "followup_error",
            "message": str(exc),
        })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.backend.app:app", host=settings.backend_host, port=settings.backend_port, reload=True)
