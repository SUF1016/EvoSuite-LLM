from __future__ import annotations

import json
import http.client
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class LLMClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError


class DryRunLLMClient(LLMClient):
    def complete(self, messages: list[dict[str, str]]) -> str:
        return "NO_CHANGE"


class FileLLMClient(LLMClient):
    def __init__(self, response_file: Path) -> None:
        self.response_file = response_file

    def complete(self, messages: list[dict[str, str]]) -> str:
        return self.response_file.read_text(encoding="utf-8")


class OpenAICompatibleClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.2,
        timeout_seconds: int = 120,
        max_tokens: int | None = None,
        extra_body: dict[str, Any] | None = None,
        retries: int = 1,
        retry_delay_seconds: float = 3.0,
    ) -> None:
        if not api_key:
            raise ValueError(
                "llm.api_key is empty. Set OPENAI_API_KEY, set llm.api_key in config, "
                "or enable llm.dry_run for pipeline smoke tests."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.extra_body = extra_body or {}
        self.retries = max(1, retries)
        self.retry_delay_seconds = retry_delay_seconds

    def complete(self, messages: list[dict[str, str]]) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        payload.update(self.extra_body)
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        last_error: BaseException | None = None
        for attempt in range(1, self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"LLM HTTP error {exc.code}: {detail}") from exc
            except (TimeoutError, socket.timeout, urllib.error.URLError, http.client.RemoteDisconnected) as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise RuntimeError(
                        f"LLM request failed after {self.retries} attempt(s): {exc}"
                    ) from exc
                time.sleep(self.retry_delay_seconds)
        else:
            raise RuntimeError(f"LLM request failed: {last_error}")
        parsed = json.loads(body)
        return parsed["choices"][0]["message"]["content"]


def make_llm_client(config: dict[str, Any]) -> LLMClient:
    llm_cfg = config.get("llm", {})
    if llm_cfg.get("dry_run", False):
        return DryRunLLMClient()
    response_file = llm_cfg.get("response_file")
    if response_file:
        return FileLLMClient(Path(response_file))
    provider = llm_cfg.get("provider", "openai-compatible")
    if provider != "openai-compatible":
        raise ValueError(f"Unsupported LLM provider: {provider}")
    return OpenAICompatibleClient(
        api_key=llm_cfg.get("api_key", ""),
        base_url=llm_cfg.get("base_url", "https://api.openai.com/v1"),
        model=llm_cfg.get("model", "gpt-4.1-mini"),
        temperature=float(llm_cfg.get("temperature", 0.2)),
        timeout_seconds=int(llm_cfg.get("timeout_seconds", 120)),
        max_tokens=llm_cfg.get("max_tokens"),
        extra_body=llm_cfg.get("extra_body", {}),
        retries=int(llm_cfg.get("retries", 1)),
        retry_delay_seconds=float(llm_cfg.get("retry_delay_seconds", 3.0)),
    )
