"""AI provider abstraction layer for Claude, OpenAI, and Ollama."""
from abc import ABC, abstractmethod
from typing import Optional
import streamlit as st

from config import OLLAMA_ENABLED


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> str:
        """Generate a response from the AI model."""
        pass


class ClaudeProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return response.content[0].text


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-5-mini"):
        import openai
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            max_completion_tokens=max_tokens,
            messages=messages
        )
        return response.choices[0].message.content


class OllamaProvider(AIProvider):
    """Local Ollama provider."""

    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        import ollama
        self.model = model
        # Note: ollama library uses default URL, custom URL requires different setup

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> str:
        import ollama
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={"num_predict": max_tokens}
        )
        return response["message"]["content"]


def get_ai_provider() -> Optional[AIProvider]:
    """Get the configured AI provider from session state."""
    provider_type = st.session_state.get("ai_provider")

    if not provider_type:
        return None

    api_key = st.session_state.get("ai_api_key")
    model = st.session_state.get("ai_model")

    try:
        if provider_type == "claude":
            return ClaudeProvider(api_key=api_key, model=model)
        elif provider_type == "openai":
            return OpenAIProvider(api_key=api_key, model=model)
        elif provider_type == "ollama":
            if not OLLAMA_ENABLED:
                st.warning("Ollama is not available in cloud deployment. Please configure Claude or OpenAI.")
                return None
            return OllamaProvider(model=model)
    except Exception as e:
        st.error(f"Failed to initialize AI provider: {e}")
        return None

    return None
