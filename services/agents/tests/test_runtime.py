import pytest

from services.agents.arrowera_agents.runtime import (
    AgentRuntime,
    CompletionResult,
    ProviderUnavailable,
)


class FailedProvider:
    name = "failed"
    model = "failed-model"

    async def complete(self, system_prompt: str, prompt: str):
        raise ProviderUnavailable("expected failure")


class WorkingProvider:
    name = "working"
    model = "working-model"

    async def complete(self, system_prompt: str, prompt: str):
        return CompletionResult(self.name, self.model, prompt, 1)


@pytest.mark.asyncio
async def test_runtime_falls_back():
    result = await AgentRuntime([FailedProvider(), WorkingProvider()]).complete("system", "prompt")
    assert result.provider == "working"


@pytest.mark.asyncio
async def test_runtime_reports_failure():
    with pytest.raises(ProviderUnavailable, match="All providers failed"):
        await AgentRuntime([FailedProvider()]).complete("system", "prompt")
