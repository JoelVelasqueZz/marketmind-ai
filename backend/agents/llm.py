"""LLMClient: capa provider-agnostica para los nodos del agente.

MODE=mock   -> respuestas deterministas sin llamadas de red, para construir y
               demostrar sin necesidad de una API key.
MODE=gemini -> Gemini API (motor principal, gratis para el equipo via Google
               AI Pro estudiantil).
MODE=claude -> Claude API como alterno, si hace falta cambiar de proveedor.

Cambiar de proveedor es una sola variable de entorno (LLM_MODE); el resto del
codigo (nodos del grafo, servicios, routers) no conoce el proveedor.
"""
from __future__ import annotations

from typing import Type, TypeVar

from pydantic import BaseModel

from backend.config import ANTHROPIC_API_KEY, GOOGLE_API_KEY, LLM_MODE, LLM_MODEL

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, mode: str | None = None, model: str | None = None) -> None:
        self.mode = mode or LLM_MODE
        self.model = model or LLM_MODEL

    def generate_structured(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        if self.mode == "gemini":
            return self._generate_gemini(system_prompt, user_prompt, schema)
        if self.mode == "claude":
            return self._generate_claude(system_prompt, user_prompt, schema)
        return self._generate_mock(system_prompt, user_prompt, schema)

    # --- Gemini ---
    def _generate_gemini(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GOOGLE_API_KEY)
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
        parsed = response.parsed
        if parsed is None:
            return schema.model_validate_json(response.text)
        return parsed

    # --- Claude (alterno) ---
    def _generate_claude(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.parse(
            model=self.model if "claude" in self.model else "claude-sonnet-5",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            response_format=schema,
        )
        return message.parsed

    # --- Mock (determinista, sin red) ---
    def _generate_mock(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        from backend.agents.mock_llm import mock_response

        return mock_response(schema, user_prompt)
