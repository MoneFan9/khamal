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
        "Your goal is to analyze application logs to perform a Root Cause Analysis (RCA).\n\n"
        "Guidelines:\n"
        "1. **Think step-by-step**: Before providing the final RCA, mentally analyze the sequence of events in the logs.\n"
        "2. **Evidence-based**: Only claim a root cause if there is direct evidence in the logs. If unsure, state multiple possibilities.\n"
        "3. **Anti-Hallucination**: Do not invent logs, file paths, or error messages that are not present in the provided context.\n"
        "4. **Conciseness**: Be technical and direct. Avoid fluff.\n"
        "5. **Actionable**: Provide specific commands or code snippets for resolution."
    )

    TOOL_ENABLED_SYSTEM_PROMPT = (
        SYSTEM_PROMPT +
        "\n\n**Tool Usage (propose_fix)**:\n"
        "- If you identify a definitive fix, use the 'propose_fix' tool.\n"
        "- Ensure the 'search_block' is an EXACT match of the code in the file. If you are unsure of the exact block, provide the full 'content' and set 'search_block' to null.\n"
        "- The output must be valid, deterministic JSON."
    )

    RCA_TEMPLATE = """
### Environment Context
- **Project Name**: {project_name}
- **Primary Language/Framework**: {language}
- **Deployment Environment**: {environment}

### Task
Analyze the following preprocessed logs to perform a technical Root Cause Analysis (RCA).

### Instructions
1. **Analyze logs**: Look for exceptions, stack traces, and error codes.
2. **Problem Summary**: Briefly describe the visible failure.
3. **Root Cause Analysis**: Identify the underlying issue based on log evidence.
4. **Actionable Resolution**: Provide the exact steps to fix the issue.

### Logs (Chronological)
```
{logs}
```

---
**Response Format**: Use clear Markdown headers.
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

    def _get_merged_context(self, project_context: Optional[dict[str, str]]) -> dict[str, str]:
        """
        Returns the merged project context with default values.
        """
        context = {
            "project_name": "Unknown",
            "language": "Auto-detected",
            "environment": "Production",
        }
        if project_context:
            context.update({k: v for k, v in project_context.items() if k in self.KNOWN_CONTEXT_KEYS})
        return context

    def _format_logs(self, logs: list[str]) -> str:
        """
        Sanitizes, joins, and truncates logs if necessary.
        """
        sanitized_logs = [str(log).strip() for log in (logs or []) if log is not None]
        if not sanitized_logs:
            raise ValueError("logs must be a non-empty list of strings.")

        formatted_logs = "\n".join(sanitized_logs)
        if len(formatted_logs) > self.max_log_chars:
            return f"... [truncated — showing last portion] ...\n{formatted_logs[-self.max_log_chars:]}"
        return formatted_logs

    def build_prompt(
        self,
        logs: list[str],
        project_context: Optional[dict[str, str]] = None
    ) -> RCAPrompt:
        """
        Formats logs and context into a structured RCAPrompt.
        """
        context = self._get_merged_context(project_context)
        formatted_logs = self._format_logs(logs)

        user_content = self._rca_template.format(
            project_name=context["project_name"],
            language=context["language"],
            environment=context["environment"],
            logs=formatted_logs
        )
        return RCAPrompt(system=self.system_prompt, user=user_content)

    def get_system_prompt(self) -> str:
        """
        Legacy method kept for compatibility with components expecting it.
        """
        return self.system_prompt

    def __repr__(self) -> str:
        return (
            f"RCAPromptBuilder("
            f"max_log_chars={self.max_log_chars}, "
            f"enable_tools={self.enable_tools}, "
            f"custom_system_prompt={self.system_prompt not in (self.SYSTEM_PROMPT, self.TOOL_ENABLED_SYSTEM_PROMPT)})"
        )
