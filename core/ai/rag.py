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
        "You are an expert DevOps and System Reliability Engineer (SRE) specializing in Root Cause Analysis (RCA).\n\n"
        "Your mission is to diagnose application crashes by analyzing preprocessed logs and project context. "
        "Adhere to these strict operational guidelines:\n\n"
        "1. **Chain-of-Thought (CoT)**: Analyze the logs chronologically. Identify the first sign of failure and track how it propagates. "
        "Distinguish between symptoms (e.g., '500 Internal Server Error') and root causes (e.g., 'OperationalError: connection to server at \"db\" failed').\n"
        "2. **Strict Evidence-Based Reasoning**: Only claim a root cause if supported by explicit log evidence. "
        "If multiple causes are possible, rank them by probability. If the root cause is absent from the logs, state 'Root cause not found in provided logs' and suggest further diagnostic steps.\n"
        "3. **Anti-Hallucination Protocol**: Never invent file paths, environment variables, or stack traces. "
        "Reference ONLY what is present in the provided context.\n"
        "4. **Pattern Recognition**: Specifically look for indicators of:\n"
        "   - Resource exhaustion (OOM, Disk Full).\n"
        "   - Infrastructure failures (Database/Redis down, DNS failure).\n"
        "   - Application logic errors (SyntaxError, AttributeError, ValueError).\n"
        "   - Configuration mismatches (Missing environment variables, incorrect ports).\n"
        "5. **Actionable Precision**: Solutions must be technical, direct, and include exact code or configuration changes."
    )

    TOOL_ENABLED_SYSTEM_PROMPT = (
        SYSTEM_PROMPT +
        "\n\n**Tool Execution (propose_fix)**:\n"
        "- Use the 'propose_fix' tool ONLY when a definitive, non-speculative fix is identified.\n"
        "- **Deterministic JSON**: Your output must be a single, valid JSON object. No preamble, no post-execution text.\n"
        "- **The 'search_block' Rule**: If performing an 'update', the 'search_block' MUST be a verbatim, unique substring from the source file. "
        "If you cannot guarantee an exact match, provide the entire file content and set 'search_block' to null."
    )

    RCA_TEMPLATE = """
### Environment Context
- **Project**: {project_name}
- **Runtime**: {language}
- **Env**: {environment}

### Logs (Chronological)
```
{logs}
```

---

### Task
Perform a technical Root Cause Analysis (RCA) based on the logs above.

### Response Structure
1. **Problem Summary**: 1-2 sentences describing the observed failure.
2. **Technical Deep Dive**:
   - **Chronological Events**: Step-by-step breakdown of the failure sequence.
   - **Error Evidence**: Reference specific log lines or stack trace elements.
3. **Root Cause**: Definitive identification of the failure's origin.
4. **Actionable Resolution**: Specific, verifiable steps to resolve the issue (e.g., config changes, code fixes, or CLI commands).

---
**Strict Constraint**: Do not include conversational filler (e.g., "I have analyzed the logs..."). Start directly with the 'Problem Summary'.
"""

    KNOWN_CONTEXT_KEYS = {"project_name", "language", "environment"}

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        rca_template: Optional[str] = None,
        max_log_chars: int = 12000,
        enable_tools: bool = False
    ):
        self._custom_system_prompt = system_prompt
        self._rca_template = rca_template or self.RCA_TEMPLATE
        self.max_log_chars = max_log_chars
        self.enable_tools = enable_tools

    @property
    def system_prompt(self) -> str:
        """
        Dynamically returns the system prompt based on tool enablement.
        """
        if self._custom_system_prompt:
            return self._custom_system_prompt
        return self.TOOL_ENABLED_SYSTEM_PROMPT if self.enable_tools else self.SYSTEM_PROMPT

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

    def __repr__(self) -> str:
        return (
            f"RCAPromptBuilder("
            f"max_log_chars={self.max_log_chars}, "
            f"enable_tools={self.enable_tools}, "
            f"custom_system_prompt={self.system_prompt not in (self.SYSTEM_PROMPT, self.TOOL_ENABLED_SYSTEM_PROMPT)})"
        )
