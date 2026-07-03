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

    def _add_anchors(self, scored_indices: List[tuple], selected_indices: set):
        """Phase 1: Add high-severity logs themselves first (anchors)."""
        for score, i in scored_indices:
            if score >= 80:
                if len(selected_indices) < self.max_output_lines:
                    selected_indices.add(i)
            else:
                break

    def _add_context_window(self, scored_indices: List[tuple], selected_indices: set, total_logs: int):
        """Phase 2: Add context window around high-severity logs."""
        for score, i in scored_indices:
            if score < 80:
                break

            context = range(max(0, i - self.context_window), min(total_logs, i + self.context_window + 1))
            for j in context:
                if len(selected_indices) >= self.max_output_lines:
                    return
                selected_indices.add(j)

    def _fill_remaining_quota(self, scored_indices: List[tuple], selected_indices: set):
        """Phase 3: Fill remaining space with other logs by priority."""
        for _, i in scored_indices:
            if len(selected_indices) >= self.max_output_lines:
                break
            if i not in selected_indices:
                selected_indices.add(i)

    def _prioritize_logs(self, logs: List[str]) -> List[str]:
        """
        Implementation of the Multi-Phase Prioritization Strategy (MPPS).

        ### 🧠 The Problem: Context Window vs. Noise
        Local LLMs have limited context windows and performance degrades with noise.
        Raw logs are often 95% "heartbeats" or "info" and 5% critical signal.
        MPPS extracts that 5% while maintaining the necessary context for RCA.

        ### 🏗️ Algorithm Phases:
        1. **Phase 1: Anchors (Ground Zero)**:
           Identifies lines with high severity scores (>= 80, e.g., CRITICAL, SIGSEGV).
           These are the definitive failure points.
        2. **Phase 2: Proximity (Stack Traces)**:
           Expands around each anchor by `context_window` lines.
           *Why?* The lines *preceding* an error (the stack trace) are usually more
           informative for the AI than the error message itself.
        3. **Phase 3: Recency-Weighted Relevance**:
           Fills the remaining `max_output_lines` quota using a hybrid score:
           `Severity + (Index / Total_Logs) * 10`.
           *Why?* It prioritizes late-occurring warnings over early-occurring ones,
           assuming the most recent logs are most relevant to the current crash.
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

        # Re-sort chronologically
        return [logs[i] for i in sorted(list(selected_indices))]

    def process(self, raw_logs: str) -> List[str]:
        """
        Main algorithm: filters noise, deduplicates, and prioritizes critical errors.
        Uses generators for memory efficiency.
        """
        if not raw_logs:
            return []

        # Use generator expressions to reduce memory overhead
        lines = (line.strip() for line in raw_logs.splitlines() if line.strip())
        filtered = (line for line in lines if not self.is_noise(line))

        # Deduplicate using a generator-friendly approach
        def gen_deduplicate(iterable):
            prev = None
            for item in iterable:
                if item != prev:
                    yield item
                prev = item

        deduplicated_gen = gen_deduplicate(filtered)

        # Convert to list only when necessary for prioritization or if small enough
        # We need a list for _prioritize_logs because it uses indices and multiple passes
        deduplicated = []
        for i, log in enumerate(deduplicated_gen):
            deduplicated.append(log)
            # If we are already under the limit and only have a few more, we might still want to list it
            # But the logic below will handle it.

        if len(deduplicated) <= self.max_output_lines:
            return deduplicated

        return self._prioritize_logs(deduplicated)
