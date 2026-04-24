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
        Removes identical consecutive log lines or highly similar ones
        to handle log bursts.
        """
        if not logs:
            return []

        unique_logs = []
        last_log = None

        for log in logs:
            # Basic deduplication: ignore exact repeats
            if log != last_log:
                unique_logs.append(log)
                last_log = log

        return unique_logs

    def process(self, raw_logs: str) -> List[str]:
        """
        Main algorithm:
        1. Split into lines
        2. Filter out noise
        3. Deduplicate
        4. Sort/Prioritize critical errors if we exceed max_output_lines
        """
        if not raw_logs:
            return []

        lines = [line.strip() for line in raw_logs.splitlines() if line.strip()]

        # 1. Filter noise
        filtered = [line for line in lines if not self.is_noise(line)]

        # 2. Deduplicate
        deduplicated = self.deduplicate(filtered)

        # 3. If still too many, prioritize by severity
        if len(deduplicated) > self.max_output_lines:
            # Keep track of original order but score them
            scored_logs = []
            for i, log in enumerate(deduplicated):
                score = self.get_severity_score(log)
                # Boost recent logs slightly to keep context (recency bias)
                recency_bonus = (i / len(deduplicated)) * 10
                scored_logs.append((score + recency_bonus, i, log))

            # Sort by score descending
            scored_logs.sort(key=lambda x: x[0], reverse=True)

            # Take top N
            top_logs = scored_logs[:self.max_output_lines]

            # Re-sort by original index to maintain chronological order
            top_logs.sort(key=lambda x: x[1])

            return [log for score, index, log in top_logs]

        return deduplicated
