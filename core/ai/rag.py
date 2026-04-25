import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class RCAPrompt:
    """
    Represents a complete prompt for RCA, including system and user messages.
    """
    system: str
    user: str

    def to_ollama_messages(self) -> list[dict[str, str]]:
        """
        Returns the messages list expected by Ollama's chat API.
        """
        return [
            {"role": "system", "content": self.system},
            {"role": "user", "content": self.user},
        ]

class RCAPromptBuilder:
    """
    Builds structured prompts for Root Cause Analysis (RCA) using logs
    and project context.
    """

    SYSTEM_PROMPT = (
        "You are an expert DevOps and System Reliability Engineer (SRE). "
        "Your goal is to analyze application logs to perform a Root Cause Analysis (RCA). "
        "Be concise, technical, and provide actionable solutions."
    )

    TOOL_ENABLED_SYSTEM_PROMPT = (
        SYSTEM_PROMPT +
        " If you identify a clear code or configuration fix, use the 'propose_fix' tool "
        "to suggest a structured JSON patch."
    )

    RCA_TEMPLATE = """
### Context
- **Project**: {project_name}
- **Language/Framework**: {language}
- **Environment**: {environment}

### Analysis Request
The following logs have been preprocessed to isolate the most relevant error signals.
Please analyze them and provide:
1. **Problem Summary**: What exactly is failing?
2. **Root Cause Identification**: Why is it failing? (e.g., missing dependency, DB connection timeout, syntax error)
3. **Actionable Resolution**: How can the user fix this? Provide code snippets or commands if applicable.

### Logs
```
{logs}
```
"""

    KNOWN_CONTEXT_KEYS = {"project_name", "language", "environment"}

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        rca_template: Optional[str] = None,
        max_log_chars: int = 12000,
        enable_tools: bool = False
    ):
        self.system_prompt = system_prompt or (self.TOOL_ENABLED_SYSTEM_PROMPT if enable_tools else self.SYSTEM_PROMPT)
        self._rca_template = rca_template or self.RCA_TEMPLATE
        self.max_log_chars = max_log_chars
        self.enable_tools = enable_tools

    def build_prompt(
        self,
        logs: list[str],
        project_context: Optional[dict[str, str]] = None
    ) -> RCAPrompt:
        """
        Formats logs and context into a structured RCAPrompt.
        """
        sanitized_logs = [str(log).strip() for log in (logs or []) if log is not None]
        if not sanitized_logs:
            raise ValueError("logs must be a non-empty list of strings.")

        context = {
            "project_name": "Unknown",
            "language": "Auto-detected",
            "environment": "Production",
        }
        if project_context:
            context.update({k: v for k, v in project_context.items() if k in self.KNOWN_CONTEXT_KEYS})

        formatted_logs = "\n".join(sanitized_logs)
        if len(formatted_logs) > self.max_log_chars:
            formatted_logs = f"... [truncated — showing last portion] ...\n{formatted_logs[-self.max_log_chars:]}"

        user_content = self._rca_template.format(
            project_name=context["project_name"],
            language=context["language"],
            environment=context["environment"],
            logs=formatted_logs
        )
        return RCAPrompt(system=self.system_prompt, user=user_content)

    def get_system_prompt(self) -> str:
        return self.system_prompt

    def __repr__(self) -> str:
        return (
            f"RCAPromptBuilder("
            f"max_log_chars={self.max_log_chars}, "
            f"enable_tools={self.enable_tools}, "
            f"custom_system_prompt={self.system_prompt not in (self.SYSTEM_PROMPT, self.TOOL_ENABLED_SYSTEM_PROMPT)})"
        )
