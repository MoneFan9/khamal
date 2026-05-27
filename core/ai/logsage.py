import re
from typing import List

class LogSagePreprocessor:
    """
    LogSage Preprocessor: The core intelligence for local crash analysis.

    This preprocessor solves the "context window" problem for LLMs. Instead of sending
    thousands of lines of logs to the local model (which is slow and memory-intensive),
    LogSage identifies "anchors" (critical errors), includes their immediate context,
    and fills the remaining quota with recent relevant logs.
    """

    # Common noise patterns in logs
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

    # Severity levels and their weights
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
        self.max_output_lines = max_output_lines
        self.context_window = context_window

    def is_noise(self, line: str) -> bool:
        """Checks if a log line is considered noise."""
        return any(pattern.search(line) for pattern in self.NOISE_PATTERNS)

    def get_severity_score(self, line: str) -> int:
        """Returns a score based on the severity found in the log line."""
        upper_line = line.upper()
        for level, score in self.SEVERITY_LEVELS.items():
            if level in upper_line:
                return score
        return 10  # Default to INFO score if not found

    def deduplicate(self, logs: List[str]) -> List[str]:
        """
        Removes identical consecutive log lines to handle log bursts.
        """
        return [log for i, log in enumerate(logs) if i == 0 or log != logs[i-1]]

    def _get_scored_indices(self, logs: List[str]) -> List[tuple]:
        """Returns indices sorted by priority score (severity + recency weight)."""
        total = len(logs)
        return sorted(
            [(self.get_severity_score(log) + (i / total) * 10, i) for i, log in enumerate(logs)],
            key=lambda x: x[0],
            reverse=True
        )

    def _prioritize_logs(self, logs: List[str]) -> List[str]:
        """
        Implementation of the Multi-Phase Prioritization Strategy (MPPS).
        Ensures local LLMs receive semantically dense information.
        """
        total_logs = len(logs)
        if not total_logs: return []

        scored_indices = self._get_scored_indices(logs)
        selected = set()

        # Phase 1: Anchors (high severity) first
        for score, i in scored_indices:
            if score < 80 or len(selected) >= self.max_output_lines: break
            selected.add(i)

        # Phase 2: Add context window around anchors
        if len(selected) < self.max_output_lines:
            for score, i in scored_indices:
                if score < 80: break
                for j in range(max(0, i - self.context_window), min(total_logs, i + self.context_window + 1)):
                    if len(selected) >= self.max_output_lines: break
                    selected.add(j)

        # Phase 3: Fill remaining quota with other logs by priority
        for _, i in scored_indices:
            if len(selected) >= self.max_output_lines: break
            selected.add(i)

        return [logs[i] for i in sorted(selected)]

    def process(self, raw_logs: str) -> List[str]:
        """Filters noise, deduplicates, and prioritizes critical errors using MPPS."""
        if not raw_logs: return []

        # Stream filtering and deduplication
        def clean_stream(logs_str):
            prev = None
            for line in logs_str.splitlines():
                line = line.strip()
                if line and line != prev and not self.is_noise(line):
                    yield line
                    prev = line

        deduplicated = list(clean_stream(raw_logs))
        if len(deduplicated) <= self.max_output_lines:
            return deduplicated

        return self._prioritize_logs(deduplicated)
