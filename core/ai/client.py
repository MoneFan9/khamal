import requests
from django.conf import settings

class OllamaClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or getattr(settings, "OLLAMA_URL", "http://localhost:11434")
        self.api_url = f"{self.base_url}/api"

    def generate(self, model, prompt, system=None, template=None, context=None, options=None, stream=False):
        """
        Generate a response for a given prompt with a provided model.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
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

    def chat(self, model, messages, options=None, stream=False):
        """
        Generate the next message in a chat with a provided model.
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
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
