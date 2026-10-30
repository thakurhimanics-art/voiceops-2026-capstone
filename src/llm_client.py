"""Unified LLM Client supporting local Ollama (default) and API providers."""
import json
import logging
import os
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL, LLM_PROVIDER, OPENAI_API_KEY, GROQ_API_KEY, GEMINI_API_KEY

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or LLM_PROVIDER or "ollama").lower()
        self.model = model or OLLAMA_MODEL
        self.base_url = OLLAMA_BASE_URL

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.1, json_mode: bool = False) -> str:
        """Execute chat completion across messages."""
        if self.provider == "ollama":
            return self._chat_ollama(messages, temperature, json_mode)
        elif self.provider in ("openai", "groq"):
            return self._chat_openai_compatible(messages, temperature, json_mode)
        elif self.provider == "gemini":
            return self._chat_gemini(messages, temperature, json_mode)
        else:
            return self._chat_ollama(messages, temperature, json_mode)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.1) -> str:
        """Simple single-prompt generation."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature)

    def _chat_ollama(self, messages: List[Dict[str, str]], temperature: float = 0.1, json_mode: bool = False) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
            }
        }
        if json_mode:
            payload["format"] = "json"

        data = json.dumps(payload).encode("utf-8")
        url = f"{self.base_url.rstrip('/')}/api/chat"
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            # Fallback to generate endpoint if chat fails
            return self._generate_ollama_fallback(messages, temperature)

    def _generate_ollama_fallback(self, messages: List[Dict[str, str]], temperature: float) -> str:
        prompt_parts = []
        for m in messages:
            prompt_parts.append(f"{m['role'].upper()}: {m['content']}")
        prompt_parts.append("ASSISTANT:")
        full_prompt = "\n\n".join(prompt_parts)

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        data = json.dumps(payload).encode("utf-8")
        url = f"{self.base_url.rstrip('/')}/api/generate"
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("response", "").strip()
        except Exception as err:
            logger.error(f"Ollama generate fallback error: {err}")
            return "I apologize, but I am currently unable to process your request."

    def _chat_openai_compatible(self, messages: List[Dict[str, str]], temperature: float, json_mode: bool) -> str:
        api_key = GROQ_API_KEY if self.provider == "groq" else OPENAI_API_KEY
        base_url = "https://api.groq.com/openai/v1" if self.provider == "groq" else "https://api.openai.com/v1"
        payload = {
            "model": self.model if self.model != OLLAMA_MODEL else ("llama-3.1-8b-instant" if self.provider == "groq" else "gpt-4o-mini"),
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{base_url}/chat/completions", data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["choices"][0]["message"]["content"].strip()

    def _chat_gemini(self, messages: List[Dict[str, str]], temperature: float, json_mode: bool) -> str:
        # Standard Gemini REST API
        gemini_model = self.model if self.model != OLLAMA_MODEL else "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={GEMINI_API_KEY}"
        contents = []
        for m in messages:
            role = "user" if m["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        payload = {"contents": contents, "generationConfig": {"temperature": temperature}}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["candidates"][0]["content"]["parts"][0]["text"].strip()
