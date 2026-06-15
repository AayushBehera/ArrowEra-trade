import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

import httpx


class ProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CompletionResult:
    provider: str
    model: str
    content: str
    duration_ms: int
    input_tokens: int = 0
    output_tokens: int = 0


class Provider(Protocol):
    name: str
    model: str

    async def complete(self, system_prompt: str, prompt: str) -> CompletionResult: ...
    async def stream(self, system_prompt: str, prompt: str) -> AsyncIterator[str]: ...


class HttpProvider:
    name = "base"

    def __init__(self, model: str, timeout: float = 45.0, retries: int = 2):
        self.model = model
        self.timeout = timeout
        self.retries = retries
        self._semaphore = asyncio.Semaphore(4)

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async with self._semaphore:
            last_error: Exception | None = None
            for attempt in range(self.retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
                except (httpx.HTTPError, httpx.TimeoutException) as exc:
                    last_error = exc
                    if attempt < self.retries:
                        await asyncio.sleep(0.5 * (2**attempt))
            raise ProviderUnavailable(f"{self.name} request failed: {last_error}")

    async def stream(self, system_prompt: str, prompt: str) -> AsyncIterator[str]:
        result = await self.complete(system_prompt, prompt)
        yield result.content


class OpenAIProvider(HttpProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str):
        super().__init__(model)
        self.api_key = api_key

    async def complete(self, system_prompt: str, prompt: str) -> CompletionResult:
        started = time.perf_counter()
        response = await self._request(
            "POST",
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "instructions": system_prompt,
                "input": prompt,
            },
        )
        payload = response.json()
        content = payload.get("output_text")
        if not content:
            content = "".join(
                item.get("text", "")
                for output in payload.get("output", [])
                for item in output.get("content", [])
                if item.get("type") == "output_text"
            )
        if not content:
            raise ProviderUnavailable("openai returned no text output")
        usage = payload.get("usage", {})
        return CompletionResult(
            provider=self.name,
            model=self.model,
            content=content,
            duration_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )

    async def stream(self, system_prompt: str, prompt: str) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "instructions": system_prompt, "input": prompt, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    event = json.loads(line[6:])
                    if event.get("type") == "response.output_text.delta":
                        yield event.get("delta", "")


class AnthropicProvider(HttpProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        super().__init__(model)
        self.api_key = api_key

    async def complete(self, system_prompt: str, prompt: str) -> CompletionResult:
        started = time.perf_counter()
        response = await self._request(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": self.model,
                "max_tokens": 2048,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        payload = response.json()
        content = "".join(block.get("text", "") for block in payload.get("content", []))
        usage = payload.get("usage", {})
        if not content:
            raise ProviderUnavailable("anthropic returned no text output")
        return CompletionResult(
            self.name,
            self.model,
            content,
            int((time.perf_counter() - started) * 1000),
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
        )


class GeminiProvider(HttpProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        super().__init__(model)
        self.api_key = api_key

    async def complete(self, system_prompt: str, prompt: str) -> CompletionResult:
        started = time.perf_counter()
        response = await self._request(
            "POST",
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            params={"key": self.api_key},
            json={
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            },
        )
        payload = response.json()
        candidates = payload.get("candidates", [])
        content = "".join(
            part.get("text", "")
            for candidate in candidates
            for part in candidate.get("content", {}).get("parts", [])
        )
        if not content:
            raise ProviderUnavailable("gemini returned no text output")
        return CompletionResult(
            self.name, self.model, content, int((time.perf_counter() - started) * 1000)
        )


class OpenAICompatibleProvider(HttpProvider):
    def __init__(self, name: str, api_key: str, model: str, base_url: str):
        super().__init__(model)
        self.name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def complete(self, system_prompt: str, prompt: str) -> CompletionResult:
        started = time.perf_counter()
        response = await self._request(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        payload = response.json()
        choices = payload.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = payload.get("usage", {})
        if not content:
            raise ProviderUnavailable(f"{self.name} returned no text output")
        return CompletionResult(
            self.name,
            self.model,
            content,
            int((time.perf_counter() - started) * 1000),
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )


class OllamaProvider(HttpProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str):
        super().__init__(model, timeout=120)
        self.base_url = base_url.rstrip("/")

    async def complete(self, system_prompt: str, prompt: str) -> CompletionResult:
        started = time.perf_counter()
        response = await self._request(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        content = response.json().get("message", {}).get("content", "")
        if not content:
            raise ProviderUnavailable("ollama returned no text output")
        return CompletionResult(
            self.name, self.model, content, int((time.perf_counter() - started) * 1000)
        )


class AgentRuntime:
    def __init__(self, providers: list[Provider]):
        self.providers = providers

    @classmethod
    def from_settings(cls, settings) -> "AgentRuntime":
        available: dict[str, Provider] = {}
        if settings.openai_api_key:
            available["openai"] = OpenAIProvider(settings.openai_api_key, settings.openai_model)
        if settings.anthropic_api_key:
            available["anthropic"] = AnthropicProvider(
                settings.anthropic_api_key, settings.anthropic_model
            )
        if settings.gemini_api_key:
            available["gemini"] = GeminiProvider(settings.gemini_api_key, settings.gemini_model)
        if settings.deepseek_api_key:
            available["deepseek"] = OpenAICompatibleProvider(
                "deepseek",
                settings.deepseek_api_key,
                settings.deepseek_model,
                "https://api.deepseek.com",
            )
        available["ollama"] = OllamaProvider(settings.ollama_base_url, settings.ollama_model)
        return cls([available[name] for name in settings.llm_provider_order if name in available])

    async def complete(
        self, system_prompt: str, prompt: str, requested_provider: str | None = None
    ) -> CompletionResult:
        providers = self.providers
        if requested_provider:
            providers = [provider for provider in providers if provider.name == requested_provider]
        if not providers:
            raise ProviderUnavailable("No configured provider matches the request")
        failures = []
        for provider in providers:
            try:
                return await provider.complete(system_prompt, prompt)
            except ProviderUnavailable as exc:
                failures.append(str(exc))
        raise ProviderUnavailable("All providers failed: " + "; ".join(failures))
