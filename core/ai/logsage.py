import re
from typing import List

class LogSagePreprocessor:
    """
    LogSage Preprocessor algorithm to filter noise and isolate critical errors
    from raw container logs.
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
        if len(selected_indices) < self.max_output_lines:
            for score, i in scored_indices:
                if score >= 80:
                    context = range(max(0, i - self.context_window), min(total_logs, i + self.context_window + 1))
                    for j in context:
                        if j not in selected_indices:
                            selected_indices.add(j)
                            if len(selected_indices) >= self.max_output_lines:
                                return
                if len(selected_indices) >= self.max_output_lines:
                    return

    def _fill_remaining_quota(self, scored_indices: List[tuple], selected_indices: set):
        """Phase 3: Fill remaining space with other logs by priority."""
        for _, i in scored_indices:
            if len(selected_indices) >= self.max_output_lines:
                break
            if i not in selected_indices:
                selected_indices.add(i)

    def _prioritize_logs(self, logs: List[str]) -> List[str]:
        """
        Prioritizes logs by severity with a recency bias to maintain context.
        Also includes context_window around high-severity logs.
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
