import requests
from django.conf import settings
from contextlib import contextmanager

class OllamaClient:
    """
    OllamaClient: High-level interface for local AI orchestration.

    Architectural Security & Performance Notes:
    1. Memory Sovereignty: Khamal is optimized for 8GB RAM. This client uses a short
       30s keep-alive window (and 'keep_alive: 0' via session cleanup) to release
       GPU/RAM resources as fast as possible.
    2. Local-First: All inference is performed on-premise. No data leaves the server.
    3. Session Management: Use the 'session' context manager to ensure automatic
       memory cleanup.
    """
    def __init__(self, base_url=None):
        self.base_url = base_url or getattr(settings, "OLLAMA_URL", "http://localhost:11434")
        self.keep_alive = getattr(settings, "OLLAMA_KEEP_ALIVE", "5m")
        self.api_url = f"{self.base_url}/api"

    def generate(self, model, prompt, system=None, template=None, context=None, options=None, stream=False, keep_alive=None):
        """
        Generate a response for a given prompt with a provided model.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "keep_alive": keep_alive if keep_alive is not None else self.keep_alive,
        }
        if system:
            payload["system"] = system
        if template:
            payload["template"] = template
        if context:
            payload["context"] = context
        if options:
            payload["options"] = options

        response = requests.post(f"{self.api_url}/generate", json=payload)
        response.raise_for_status()

        if stream:
            return response.iter_lines()
        return response.json()

    def chat(self, model, messages, tools=None, options=None, stream=False, keep_alive=None):
        """
        Generate the next message in a chat with a provided model.
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "keep_alive": keep_alive if keep_alive is not None else self.keep_alive,
        }
        if tools:
            payload["tools"] = tools
        if options:
            payload["options"] = options

        response = requests.post(f"{self.api_url}/chat", json=payload)
        response.raise_for_status()

        if stream:
            return response.iter_lines()
        return response.json()

    def list_models(self):
        """
        List models that are available locally.
        """
        response = requests.get(f"{self.api_url}/tags")
        response.raise_for_status()
        return response.json()

    def pull_model(self, name, stream=False):
        """
        Download a model from the ollama library.
        """
        payload = {"name": name, "stream": stream}
        response = requests.post(f"{self.api_url}/pull", json=payload)
        response.raise_for_status()

        if stream:
            return response.iter_lines()
        return response.json()

    def show_model(self, name):
        """
        Show information about a model.
        """
        payload = {"name": name}
        response = requests.post(f"{self.api_url}/show", json=payload)
        response.raise_for_status()
        return response.json()

    def unload_model(self, model):
        """
        Unload a model from memory by setting keep_alive to 0.
        """
        payload = {
            "model": model,
            "keep_alive": 0
        }
        response = requests.post(f"{self.api_url}/generate", json=payload)
        response.raise_for_status()
        return response.json()

    @contextmanager
    def session(self, model):
        """
        Context manager to ensure the model is unloaded from memory
        after the request is completed.
        """
        try:
            yield self
        finally:
            try:
                self.unload_model(model)
            except Exception:
                pass
