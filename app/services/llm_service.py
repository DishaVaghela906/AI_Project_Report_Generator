"""
LLM Service — Dedicated Groq Provider for Academic Chapter Generation.
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import httpx
from loguru import logger

from app.core.config import settings
from app.services.prompt_builder import get_chapter_title

SYSTEM_PROMPT = """You are a senior academic technical writer helping engineering students write formal university project reports.

Your writing must feel like it was written by a knowledgeable, hardworking student — not by an AI tool.

Key rules you MUST follow without exception:
1. NEVER start a section with generic AI-sounding openers like "In today's rapidly evolving world", "Leveraging cutting-edge technologies", "In the modern era", or "This project aims to harness the power of".
2. Write every section grounded in the SPECIFIC project — use the actual project title, module names, database table names, tech stack names, and feature names provided in the prompt.
3. Use natural academic phrases like: "The development team identified...", "During the analysis phase, it was observed that...", "The system was designed to address...", "Testing revealed that...", "As shown in Figure X.X...".
4. Each section must have a clear, numbered heading and at least 3 well-developed paragraphs.
5. Functional requirements must follow the format: "The system shall allow the user to [action]."
6. Test cases must be in a table with: Test Case ID | Description | Input | Expected Output | Actual Output | Status.
7. References must be in IEEE citation format.
8. The report follows the MSU Baroda Faculty of Technology & Engineering, Department of Computer Science and Engineering project report format exactly.
9. Output must be in clean, well-structured Markdown — headings, bullet points, numbered lists, and tables where appropriate.
10. The content must read as if a dedicated engineering student who deeply understands their project wrote it over many weeks."""


# ─── Public API ───────────────────────────────────────────────────────────────

async def generate_chapter(
    chapter_number: int,
    prompt: str,
) -> str:
    """
    Generate a chapter using Groq API.
    """
    chapter_title = get_chapter_title(chapter_number)
    logger.info(
        f"Generating Chapter {chapter_number} ({chapter_title}) "
        f"via Groq model='{settings.GROQ_MODEL}'"
    )

    return await _generate_via_openai_compatible(
        url="https://api.groq.com/openai/v1/chat/completions",
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        prompt=prompt,
        chapter_number=chapter_number,
    )


async def stream_chapter(
    chapter_number: int,
    prompt: str,
) -> AsyncIterator[str]:
    """
    Stream-generate a chapter token-by-token (for SSE endpoints) via Groq.
    """
    logger.info(f"Streaming Chapter {chapter_number} via Groq model='{settings.GROQ_MODEL}'")

    async for token in _stream_via_openai_compatible(
        url="https://api.groq.com/openai/v1/chat/completions",
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        prompt=prompt,
    ):
        yield token


async def check_llm_health() -> dict:
    """Check status of Groq LLM provider."""
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


async def check_ollama_health() -> bool:
    """Backward compatibility alias."""
    status = await check_llm_health()
    return status.get("ready", False)


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _resolve_provider_info(chapter_number: int = 1) -> tuple[str, str, str]:
    """Returns provider info ('groq', api_key, model)."""
    return "groq", settings.GROQ_API_KEY, settings.GROQ_MODEL


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
            f"GROQ_API_KEY is missing in your .env file. "
            "Please configure your Groq API key to generate chapters."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    max_tokens = settings.LLM_MAX_TOKENS

    async with httpx.AsyncClient(timeout=180.0) as client:
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
        raise ValueError("GROQ_API_KEY is missing in your .env file.")

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
