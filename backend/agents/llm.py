"""LLMClient: capa provider-agnostica para los nodos del agente.

MODE=mock     -> respuestas deterministas sin llamadas de red, para construir y
                 demostrar sin necesidad de una API key.
MODE=gemini   -> Gemini API (motor principal, gratis para el equipo via Google
                 AI Pro estudiantil).
MODE=claude   -> Claude API como alterno, si hace falta cambiar de proveedor.
MODE=deepseek -> DeepSeek API (u OpenRouter, que expone el mismo formato) como
                 alterno gratuito si se agota la cuota de Gemini.

Cambiar de proveedor es una sola variable de entorno (LLM_MODE); el resto del
codigo (nodos del grafo, servicios, routers) no conoce el proveedor.
"""
from __future__ import annotations

import json
import time
from typing import Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

from backend.config import (
    ANTHROPIC_API_KEY,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    GOOGLE_API_KEY,
    LLM_MODE,
    LLM_MODEL,
)

T = TypeVar("T", bound=BaseModel)

MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 1.5


class TransientLLMError(Exception):
    """Fallo transitorio del proveedor de LLM (503/429) tras agotar los reintentos."""


class LLMOutputInvalid(Exception):
    """El proveedor devolvio una salida que no valida contra el schema.

    Se descarta por seguridad en vez de publicarla: preferimos fallar honesto
    a mostrar una senal con datos malformados (mitigacion de riesgos).
    """


def _with_retry(call: Callable[[], T], is_transient: Callable[[Exception], bool]) -> T:
    """Reintenta con backoff exponencial ante errores transitorios (503/429) del proveedor.

    No reintenta errores de cliente (modelo invalido, request mal formado, etc.) — esos
    fallan de inmediato porque reintentarlos no cambia el resultado.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001 - reevaluado abajo via is_transient
            if not is_transient(exc):
                raise
            if attempt == MAX_ATTEMPTS:
                raise TransientLLMError(
                    f"El proveedor de LLM no respondio tras {MAX_ATTEMPTS} intentos: {exc}"
                ) from exc
            time.sleep(BASE_DELAY_SECONDS * (2 ** (attempt - 1)))
    raise AssertionError("unreachable")  # pragma: no cover


class LLMClient:
    def __init__(self, mode: str | None = None, model: str | None = None) -> None:
        self.mode = mode or LLM_MODE
        self.model = model or LLM_MODEL
        # Telemetria de la ultima llamada para la traza de ejecucion:
        # intentos, y tokens reportados por el proveedor (measured=True) o
        # estimados len/4 en mock (measured=False).
        self._last_attempts = 0
        self._last_usage: dict | None = None

    def _counted(self, call: Callable[[], T]) -> Callable[[], T]:
        def wrapped() -> T:
            self._last_attempts += 1
            return call()

        return wrapped

    def generate_structured(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        self._last_attempts = 0
        self._last_usage = None
        try:
            if self.mode == "gemini":
                return self._generate_gemini(system_prompt, user_prompt, schema)
            if self.mode == "claude":
                return self._generate_claude(system_prompt, user_prompt, schema)
            if self.mode == "deepseek":
                return self._generate_deepseek(system_prompt, user_prompt, schema)
            self._last_attempts = 1
            result = self._generate_mock(system_prompt, user_prompt, schema)
            # Mock: sin red, tokens estimados (len/4) y honestamente marcados.
            self._last_usage = {
                "tokens_in": (len(system_prompt) + len(user_prompt)) // 4,
                "tokens_out": len(result.model_dump_json()) // 4,
                "measured": False,
            }
            return result
        except (ValidationError, json.JSONDecodeError) as exc:
            raise LLMOutputInvalid(
                f"La salida del proveedor '{self.mode}' no valida contra {schema.__name__}: {exc}"
            ) from exc

    def _record_usage(self, tokens_in, tokens_out) -> None:
        if tokens_in is None or tokens_out is None:
            return
        self._last_usage = {
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "measured": True,
        }

    # --- Gemini ---
    def _generate_gemini(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        from google import genai
        from google.genai import errors as genai_errors
        from google.genai import types

        client = genai.Client(api_key=GOOGLE_API_KEY)

        def call() -> T:
            response = client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.2,
                ),
            )
            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                self._record_usage(
                    getattr(usage, "prompt_token_count", None),
                    getattr(usage, "candidates_token_count", None),
                )
            parsed = response.parsed
            if parsed is None:
                return schema.model_validate_json(response.text)
            return parsed

        def is_transient(exc: Exception) -> bool:
            if isinstance(exc, genai_errors.ServerError):
                return True
            code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
            return isinstance(exc, genai_errors.ClientError) and code == 429

        return _with_retry(self._counted(call), is_transient)

    # --- Claude (alterno) ---
    def _generate_claude(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        # anthropic==0.40.0 no tiene messages.parse: se fuerza JSON via prompt
        # con el JSON Schema (mismo patron que DeepSeek) y se valida con Pydantic.
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        schema_prompt = (
            f"{system_prompt}\n\nResponde EXCLUSIVAMENTE con un JSON valido (sin texto extra, sin "
            f"markdown) que cumpla este JSON Schema:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )

        def call() -> T:
            message = client.messages.create(
                model=self.model if "claude" in self.model else "claude-sonnet-5",
                max_tokens=1024,
                temperature=0.2,
                system=schema_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            usage = getattr(message, "usage", None)
            if usage is not None:
                self._record_usage(
                    getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None)
                )
            return schema.model_validate_json(message.content[0].text)

        def is_transient(exc: Exception) -> bool:
            return isinstance(exc, (anthropic.InternalServerError, anthropic.RateLimitError, anthropic.APIConnectionError))

        return _with_retry(self._counted(call), is_transient)

    # --- DeepSeek (alterno gratuito, via API oficial u OpenRouter) ---
    def _generate_deepseek(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        import openai
        from openai import OpenAI

        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        schema_prompt = (
            f"{system_prompt}\n\nResponde EXCLUSIVAMENTE con un JSON valido (sin texto extra, sin "
            f"markdown) que cumpla este JSON Schema:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )

        def call() -> T:
            completion = client.chat.completions.create(
                model=self.model if "deepseek" in self.model else "deepseek-chat",
                messages=[
                    {"role": "system", "content": schema_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            usage = getattr(completion, "usage", None)
            if usage is not None:
                self._record_usage(
                    getattr(usage, "prompt_tokens", None), getattr(usage, "completion_tokens", None)
                )
            return schema.model_validate_json(completion.choices[0].message.content)

        def is_transient(exc: Exception) -> bool:
            return isinstance(exc, (openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError))

        return _with_retry(self._counted(call), is_transient)

    # --- Mock (determinista, sin red) ---
    def _generate_mock(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        from backend.agents.mock_llm import mock_response

        return mock_response(schema, user_prompt)
