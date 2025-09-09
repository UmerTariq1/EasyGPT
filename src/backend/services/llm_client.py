from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional, Tuple

from ..config import settings, resolve_provider_and_model


class LLMClient:
    """Unified client that routes requests to OpenAI, Gemini, DeepSeek, or a mock.

    Public API returns a tuple of (text, usage_dict) where:
      - text: the raw string returned by the provider (ideally JSON adhering to our schema)
      - usage_dict: provider/model plus token and latency metadata
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> Tuple[str, Dict[str, Any]]:
        provider_name, model_name = resolve_provider_and_model(provider, model)
        start = time.perf_counter()
        try:
            if provider_name == "openai":
                if not settings.openai_api_key:
                    raise RuntimeError("OPENAI_API_KEY is not set. Please add it to your .env or switch provider to 'mock'.")
                text, usage = self._openai_chat(
                    system_prompt, user_prompt, model_name, temperature, max_tokens
                )
            elif provider_name == "gemini":
                if not settings.gemini_api_key:
                    raise RuntimeError("GEMINI_API_KEY is not set. Please add it to your .env or switch provider to 'mock'.")
                text, usage = self._gemini_generate(
                    system_prompt, user_prompt, model_name, temperature, max_tokens
                )
            elif provider_name == "deepseek":
                if not settings.deepseek_api_key:
                    raise RuntimeError("DEEPSEEK_API_KEY is not set. Please add it to your .env or switch provider to 'mock'.")
                text, usage = self._deepseek_chat(
                    system_prompt, user_prompt, model_name, temperature, max_tokens
                )
            else:
                text, usage = self._mock(system_prompt, user_prompt)
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
        # normalize usage
        usage["latency_ms"] = elapsed_ms
        usage["provider"] = provider_name
        usage["model"] = model_name
        return text, usage

    # --- Providers -----------------------------------------------------------------

    def _openai_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Tuple[str, Dict[str, Any]]:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("openai package is not installed") from exc

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = (resp.choices[0].message.content or "") if resp.choices else ""
        usage = {
            "input_tokens": getattr(resp, "usage", None) and resp.usage.prompt_tokens,
            "output_tokens": getattr(resp, "usage", None) and resp.usage.completion_tokens,
        }
        return text, usage

    def _deepseek_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Tuple[str, Dict[str, Any]]:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("openai package is not installed") from exc

        client = OpenAI(api_key=settings.deepseek_api_key, base_url="https://api.deepseek.com/v1")
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = (resp.choices[0].message.content or "") if resp.choices else ""
        usage = {
            "input_tokens": getattr(resp, "usage", None) and resp.usage.prompt_tokens,
            "output_tokens": getattr(resp, "usage", None) and resp.usage.completion_tokens,
        }
        return text, usage

    def _gemini_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> Tuple[str, Dict[str, Any]]:
        try:
            import google.generativeai as genai  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("google-generativeai package is not installed") from exc

        genai.configure(api_key=settings.gemini_api_key)
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        model_client = genai.GenerativeModel(model)
        response = model_client.generate_content(
            [
                {"role": "system", "parts": [system_prompt]},
                {"role": "user", "parts": [user_prompt]},
            ],
            generation_config=generation_config,
        )
        text = getattr(response, "text", None) or ""
        usage = {"input_tokens": None, "output_tokens": None}
        usage_meta = getattr(response, "usage_metadata", None)
        if usage_meta:
            prompt_tokens = getattr(usage_meta, "prompt_token_count", None)
            candidates_tokens = getattr(usage_meta, "candidates_token_count", None)
            usage = {"input_tokens": prompt_tokens, "output_tokens": candidates_tokens}
        return text, usage

    def _mock(self, system_prompt: str, user_prompt: str) -> Tuple[str, Dict[str, Any]]:
        content = {
            "cards": [
                {
                    "id": "overview",
                    "title": "Overview",
                    "content": "This is a mock response demonstrating the card layout.",
                    "kind": "text",
                },
                {
                    "id": "step-1",
                    "title": "Step 1",
                    "content": "Explain step one clearly and concisely.",
                    "kind": "text",
                },
            ]
        }
        return json.dumps(content), {"input_tokens": 0, "output_tokens": 0}
