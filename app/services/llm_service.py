"""
LLM Service — Multi-Provider Support (Groq, Hugging Face, OpenRouter, Ollama).

Supports:
  - Groq API (Qwen 2.5 Coder 32B, Qwen 2.5 32B, Llama 3.3 70B, DeepSeek R1 Qwen)
  - Hugging Face Serverless / Router API (Qwen/Qwen2.5-72B-Instruct, etc.)
  - OpenRouter API
  - Local Ollama fallback
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import httpx
import ollama as ollama_sdk
from loguru import logger

from app.core.config import settings
from app.services.prompt_builder import get_chapter_title

SYSTEM_PROMPT = (
    "You are an expert academic research assistant and project report author. "
    "Write comprehensive, highly detailed, well-formatted, formal academic project report chapters. "
    "Use clear headings, markdown formatting, bullet points, technical descriptions, and architectural explanations."
)


# ─── Public API ───────────────────────────────────────────────────────────────

async def generate_chapter(
    chapter_number: int,
    prompt: str,
) -> str:
    """
    Generate a chapter using the configured LLM provider (Groq, Hugging Face, OpenRouter, or Ollama).
    """
    provider, api_key, model = _resolve_provider_info(chapter_number)
    chapter_title = get_chapter_title(chapter_number)

    logger.info(
        f"Generating Chapter {chapter_number} ({chapter_title}) "
        f"via provider='{provider}', model='{model}'"
    )

    if provider == "groq":
        return await _generate_via_openai_compatible(
            url="https://api.groq.com/openai/v1/chat/completions",
            api_key=api_key or settings.GROQ_API_KEY,
            model=model or settings.GROQ_MODEL,
            prompt=prompt,
            chapter_number=chapter_number,
        )
    elif provider in ("huggingface", "hf"):
        return await _generate_via_openai_compatible(
            url="https://router.huggingface.co/hf-inference/v1/chat/completions",
            api_key=api_key or settings.HF_API_KEY,
            model=model or settings.HF_MODEL,
            prompt=prompt,
            chapter_number=chapter_number,
        )
    elif provider == "openrouter":
        return await _generate_via_openai_compatible(
            url="https://openrouter.ai/api/v1/chat/completions",
            api_key=api_key or settings.OPENROUTER_API_KEY,
            model=model or settings.OPENROUTER_MODEL,
            prompt=prompt,
            chapter_number=chapter_number,
            extra_headers={"HTTP-Referer": "http://localhost:8000"},
        )
    else:  # default to ollama
        return await _generate_via_ollama(prompt, chapter_number)


async def stream_chapter(
    chapter_number: int,
    prompt: str,
) -> AsyncIterator[str]:
    """
    Stream-generate a chapter token-by-token (for SSE endpoints).
    """
    provider, api_key, model = _resolve_provider_info(chapter_number)
    logger.info(f"Streaming Chapter {chapter_number} via provider='{provider}'")

    if provider == "groq":
        async for token in _stream_via_openai_compatible(
            url="https://api.groq.com/openai/v1/chat/completions",
            api_key=api_key or settings.GROQ_API_KEY,
            model=model or settings.GROQ_MODEL,
            prompt=prompt,
        ):
            yield token
    elif provider in ("huggingface", "hf"):
        async for token in _stream_via_openai_compatible(
            url="https://router.huggingface.co/hf-inference/v1/chat/completions",
            api_key=api_key or settings.HF_API_KEY,
            model=model or settings.HF_MODEL,
            prompt=prompt,
        ):
            yield token
    elif provider == "openrouter":
        async for token in _stream_via_openai_compatible(
            url="https://openrouter.ai/api/v1/chat/completions",
            api_key=api_key or settings.OPENROUTER_API_KEY,
            model=model or settings.OPENROUTER_MODEL,
            prompt=prompt,
            extra_headers={"HTTP-Referer": "http://localhost:8000"},
        ):
            yield token
    else:
        async for token in _stream_via_ollama(prompt):
            yield token


async def check_llm_health() -> dict:
    """Check status of configured LLM provider."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        key = settings.GROQ_API_KEY
        if not key or key == "gsk_your_groq_api_key_here":
            return {
                "ready": False,
                "provider": "groq",
                "model": settings.GROQ_MODEL,
                "message": "GROQ_API_KEY is missing in .env file. Obtain one at https://console.groq.com/keys",
            }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {key}"},
                )
                if res.status_code == 200:
                    return {"ready": True, "provider": "groq", "model": settings.GROQ_MODEL}
                return {
                    "ready": False,
                    "provider": "groq",
                    "model": settings.GROQ_MODEL,
                    "message": f"Groq API returned HTTP {res.status_code}: {res.text[:200]}",
                }
        except Exception as exc:
            return {"ready": False, "provider": "groq", "model": settings.GROQ_MODEL, "message": str(exc)}

    elif provider in ("huggingface", "hf"):
        key = settings.HF_API_KEY
        if not key:
            return {
                "ready": False,
                "provider": "huggingface",
                "model": settings.HF_MODEL,
                "message": "HF_API_KEY is missing in .env file. Obtain token at https://huggingface.co/settings/tokens",
            }
        return {"ready": True, "provider": "huggingface", "model": settings.HF_MODEL}

    elif provider == "openrouter":
        key = settings.OPENROUTER_API_KEY
        if not key:
            return {
                "ready": False,
                "provider": "openrouter",
                "model": settings.OPENROUTER_MODEL,
                "message": "OPENROUTER_API_KEY is missing in .env file.",
            }
        return {"ready": True, "provider": "openrouter", "model": settings.OPENROUTER_MODEL}

    else:
        # Ollama local check
        try:
            client = ollama_sdk.AsyncClient(host=settings.OLLAMA_BASE_URL)
            models_response = await client.list()
            available = [m.model for m in models_response.models]
            model_ready = any(settings.OLLAMA_MODEL in m for m in available)
            return {
                "ready": model_ready,
                "provider": "ollama",
                "model": settings.OLLAMA_MODEL,
                "message": "Local Ollama ready" if model_ready else f"Model {settings.OLLAMA_MODEL} not pulled",
            }
        except Exception as exc:
            return {"ready": False, "provider": "ollama", "model": settings.OLLAMA_MODEL, "message": str(exc)}


async def check_ollama_health() -> bool:
    """Backward compatibility alias for Ollama health check."""
    status = await check_llm_health()
    return status.get("ready", False)


# ─── Private Helpers ──────────────────────────────────────────────────────────

def _resolve_provider_info(chapter_number: int) -> tuple[str, str, str]:
    """Returns (provider_name, api_key, model) for a given chapter."""
    chapter_key = settings.chapter_api_keys.get(chapter_number, "default").strip()

    if chapter_key.startswith("gsk_"):
        return "groq", chapter_key, settings.GROQ_MODEL
    elif chapter_key.startswith("hf_"):
        return "huggingface", chapter_key, settings.HF_MODEL
    elif chapter_key.startswith("sk-or-"):
        return "openrouter", chapter_key, settings.OPENROUTER_MODEL
    elif chapter_key.lower() in ("ollama", "ollama-local", "local"):
        return "ollama", "", settings.OLLAMA_MODEL

    # Fall back to system LLM_PROVIDER
    prov = settings.LLM_PROVIDER.lower()
    if prov == "groq":
        return "groq", settings.GROQ_API_KEY, settings.GROQ_MODEL
    elif prov in ("huggingface", "hf"):
        return "huggingface", settings.HF_API_KEY, settings.HF_MODEL
    elif prov == "openrouter":
        return "openrouter", settings.OPENROUTER_API_KEY, settings.OPENROUTER_MODEL
    else:
        return "ollama", "", settings.OLLAMA_MODEL


async def _generate_via_openai_compatible(
    url: str,
    api_key: str,
    model: str,
    prompt: str,
    chapter_number: int,
    extra_headers: dict | None = None,
) -> str:
    """Generate chapter using OpenAI-compatible HTTP chat completion API with 429 retry logic."""
    if not api_key:
        raise ValueError(
            f"API Key is missing for provider model '{model}'. "
            "Please configure the corresponding API key in your .env file."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    # Use configured max_tokens (default 1500 safely fits Groq rate limits)
    max_tokens = settings.LLM_MAX_TOKENS

    async with httpx.AsyncClient(timeout=180.0) as client:
        # Retry loop for rate limits (429)
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": max_tokens,
                "stream": False,
            }

            response = await client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                logger.success(f"Chapter {chapter_number} generated successfully via {model} ({len(text)} chars)")
                return text

            # Handle 429 Rate Limit (e.g., OTPM limit exceeded)
            if response.status_code == 429 and attempt < max_retries:
                logger.warning(
                    f"HTTP 429 Rate Limit on attempt {attempt}/{max_retries}. "
                    f"Reducing max_tokens from {max_tokens} to {max(600, max_tokens - 400)} and retrying in {attempt * 2}s..."
                )
                max_tokens = max(600, max_tokens - 400)
                await asyncio.sleep(attempt * 2)
                continue

            error_msg = f"LLM API Error ({response.status_code}): {response.text[:300]}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)


async def _stream_via_openai_compatible(
    url: str,
    api_key: str,
    model: str,
    prompt: str,
    extra_headers: dict | None = None,
) -> AsyncIterator[str]:
    """Stream response tokens using OpenAI-compatible SSE stream."""
    if not api_key:
        raise ValueError(f"API Key is missing for provider model '{model}'. Check your .env file.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            if response.status_code != 200:
                body = await response.aread()
                raise RuntimeError(f"Streaming LLM API Error ({response.status_code}): {body.decode()[:300]}")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue


async def _generate_via_ollama(prompt: str, chapter_number: int) -> str:
    """Fallback Ollama local generation."""
    def _sync_call() -> str:
        client = ollama_sdk.Client(host=settings.OLLAMA_BASE_URL)
        response = client.generate(
            model=settings.OLLAMA_MODEL,
            prompt=prompt,
            options={"temperature": 0.7, "top_p": 0.9, "num_predict": 4096},
            stream=False,
        )
        return response.response

    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(None, _sync_call)
    logger.success(f"Chapter {chapter_number} generated locally via Ollama ({len(text)} chars)")
    return text


async def _stream_via_ollama(prompt: str) -> AsyncIterator[str]:
    """Fallback Ollama local streaming."""
    client = ollama_sdk.AsyncClient(host=settings.OLLAMA_BASE_URL)
    async for chunk in await client.generate(
        model=settings.OLLAMA_MODEL,
        prompt=prompt,
        options={"temperature": 0.7, "top_p": 0.9, "num_predict": 4096},
        stream=True,
    ):
        if chunk.response:
            yield chunk.response
