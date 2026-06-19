import re
from typing import List

class LogSagePreprocessor:
    """
    LogSage Preprocessor: The core intelligence for local crash analysis.

    This preprocessor solves the "context window" problem for local LLMs (like Llama 3).
    Instead of sending thousands of lines of logs to the local model—which would be
    slow, memory-intensive (especially on 8GB RAM machines), and often exceed the
    model's context window—LogSage implements the Multi-Phase Prioritization Strategy (MPPS).

    MPPS identifies "anchors" (critical errors), preserves their immediate context,
    and fills the remaining quota with the most relevant logs based on severity and recency.
    """

    # Common noise patterns to filter out to save context window space
    NOISE_PATTERNS = [
        re.compile(r"heartbeat", re.I),
        re.compile(r"health\s?check", re.I),
        re.compile(r"GET\s+/health", re.I),
        re.compile(r"GET\s+/metrics", re.I),
        re.compile(r"status\s+200", re.I),
        re.compile(r"poll\s+interval", re.I),
        re.compile(r"connection\s+keep-alive", re.I),
        re.compile(r"GET\s+/favicon\.ico", re.I),
        re.compile(r"GET\s+/static/", re.I),
        re.compile(r"unimportant", re.I),
    ]

    # Severity levels and their weights for prioritization
    SEVERITY_LEVELS = {
        "CRITICAL": 100,
        "PANIC": 100,
        "FATAL": 100,
        "SIGSEGV": 100,
        "EXCEPTION": 90,
        "TRACEBACK": 90,
        "ERROR": 80,
        "WARNING": 40,
        "INFO": 10,
        "DEBUG": 0,
    }

    def __init__(self, max_output_lines: int = 100, context_window: int = 3):
        """
        Args:
            max_output_lines: Maximum number of lines to send to the LLM.
            context_window: Number of lines to include before and after an 'anchor' error.
        """
        self.max_output_lines = max_output_lines
        self.context_window = context_window

    def is_noise(self, line: str) -> bool:
        """Checks if a log line is considered noise (heartbeats, health checks, etc.)."""
        return any(pattern.search(line) for pattern in self.NOISE_PATTERNS)

    def get_severity_score(self, line: str) -> int:
        """
        Returns a score based on the severity keywords found in the log line.
        Default is 10 (INFO).
        """
        upper_line = line.upper()
        for level, score in self.SEVERITY_LEVELS.items():
            if level in upper_line:
                return score
        return 10

    def deduplicate(self, logs: List[str]) -> List[str]:
        """
        Removes identical consecutive log lines to handle log bursts/flooding.
        """
        return [log for i, log in enumerate(logs) if i == 0 or log != logs[i-1]]

    def _add_anchors(self, scored_indices: List[tuple], selected_indices: set):
        """
        Phase 1: Identify and add "Anchors" (Ground Zero).
        Anchors are high-severity logs (score >= 80) that definitively indicate a failure.
        """
        for score, i in scored_indices:
            if score >= 80:
                if len(selected_indices) < self.max_output_lines:
                    selected_indices.add(i)
            else:
                break

    def _add_context_window(self, scored_indices: List[tuple], selected_indices: set, total_logs: int):
        """
        Phase 2: Proximity Expansion.
        For every anchor, we add 'context_window' lines before and after.
        This captures the stack trace or the state leading up to the crash.
        """
        for score, i in scored_indices:
            if score < 80:
                break

            context = range(max(0, i - self.context_window), min(total_logs, i + self.context_window + 1))
            for j in context:
                if len(selected_indices) >= self.max_output_lines:
                    return
                selected_indices.add(j)

    def _fill_remaining_quota(self, scored_indices: List[tuple], selected_indices: set):
        """
        Phase 3: Recency-Weighted Relevance.
        If space remains, fill with other logs (warnings, info) prioritized by
        severity and how late they appeared in the log stream.
        """
        for _, i in scored_indices:
            if len(selected_indices) >= self.max_output_lines:
                break
            if i not in selected_indices:
                selected_indices.add(i)

    def _prioritize_logs(self, logs: List[str]) -> List[str]:
        """
        Implementation of the Multi-Phase Prioritization Strategy (MPPS).

        This algorithm ensures that local LLMs receive the most semantically dense
        information within their context window limit.

        The hybrid scoring (Severity + (Index / Total) * 10) ensures that
        late-occurring warnings take precedence over early-occurring ones.
        """
        total_logs = len(logs)
        if total_logs == 0:
            return []

        scored_indices = sorted(
            [
                (self.get_severity_score(log) + (i / total_logs) * 10, i)
                for i, log in enumerate(logs)
            ],
            key=lambda x: x[0],
            reverse=True
        )

        selected_indices = set()

        self._add_anchors(scored_indices, selected_indices)
        self._add_context_window(scored_indices, selected_indices, total_logs)
        self._fill_remaining_quota(scored_indices, selected_indices)

        # Re-sort chronologically to maintain the log sequence for the AI
        return [logs[i] for i in sorted(list(selected_indices))]

    def process(self, raw_logs: str) -> List[str]:
        """
        Main processing pipeline:
        1. Split into lines and strip whitespace.
        2. Filter out noise (heartbeats, etc.).
        3. Deduplicate consecutive identical lines.
        4. Apply MPPS if the log count exceeds the limit.
        """
        if not raw_logs:
            return []

        # Use generators for memory efficiency on large log streams
        lines = (line.strip() for line in raw_logs.splitlines() if line.strip())
        filtered = (line for line in lines if not self.is_noise(line))

        def gen_deduplicate(iterable):
            prev = None
            for item in iterable:
                if item != prev:
                    yield item
                prev = item

        deduplicated_gen = gen_deduplicate(filtered)

        # Materialize to list for indexing and prioritization
        deduplicated = list(deduplicated_gen)

        if len(deduplicated) <= self.max_output_lines:
            return deduplicated

        return self._prioritize_logs(deduplicated)
