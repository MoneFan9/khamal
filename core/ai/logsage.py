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
    ]

    # Severity levels and their weights
    SEVERITY_LEVELS = {
        "CRITICAL": 100,
        "FATAL": 100,
        "ERROR": 80,
        "WARNING": 40,
        "INFO": 10,
        "DEBUG": 0,
    }

    def __init__(self, max_output_lines: int = 100):
        self.max_output_lines = max_output_lines

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

    def process(self, raw_logs: str) -> List[str]:
        """
        Main algorithm: filters noise, deduplicates, and prioritizes critical errors.
        """
        if not raw_logs:
            return []

        lines = [line.strip() for line in raw_logs.splitlines() if line.strip()]
        filtered = [line for line in lines if not self.is_noise(line)]
        deduplicated = self.deduplicate(filtered)

        if len(deduplicated) <= self.max_output_lines:
            return deduplicated

        # Prioritize by severity with a recency bias to maintain context
        scored_logs = sorted(
            [
                (self.get_severity_score(log) + (i / len(deduplicated)) * 10, i, log)
                for i, log in enumerate(deduplicated)
            ],
            key=lambda x: x[0],
            reverse=True
        )[:self.max_output_lines]

        # Re-sort chronologically
        return [log for _, i, log in sorted(scored_logs, key=lambda x: x[1])]
