from collections import Counter
from datetime import datetime
from typing import Iterable


class LogStatistics:

    def __init__(self):
        self.total_events = 0

        self.agents = Counter()
        self.decoders = Counter()
        self.rule_levels = Counter()

        self.source_ips = Counter()
        self.destination_ips = Counter()

        self.first_timestamp = None
        self.last_timestamp = None

    def process(self, log: dict) -> None:
        """Process one normalized log event."""

        self.total_events += 1

        # Agent
        if log["agent_name"]:
            self.agents[log["agent_name"]] += 1

        # Decoder
        if log["decoder"]:
            self.decoders[log["decoder"]] += 1

        # Rule level
        if log["rule_level"] is not None:
            self.rule_levels[log["rule_level"]] += 1

        # Source IP
        if log["source_ip"]:
            self.source_ips[log["source_ip"]] += 1

        # Destination IP
        if log["destination_ip"]:
            self.destination_ips[log["destination_ip"]] += 1

        # Timestamp
        timestamp = self._parse_timestamp(log["timestamp"])

        if timestamp:
            if self.first_timestamp is None:
                self.first_timestamp = timestamp

            self.last_timestamp = timestamp

    def process_logs(self, logs: Iterable[dict]) -> None:
        """Process a stream of normalized logs."""

        for log in logs:
            self.process(log)

    @staticmethod
    def _parse_timestamp(timestamp):
        if not timestamp:
            return None

        try:
            return datetime.strptime(
                timestamp,
                "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        except ValueError:
            return None

    def duration_seconds(self):
        if not self.first_timestamp or not self.last_timestamp:
            return None

        return (
            self.last_timestamp - self.first_timestamp
        ).total_seconds()

    def events_per_second(self):
        duration = self.duration_seconds()

        if not duration or duration <= 0:
            return None

        return self.total_events / duration

    def report(self, top_n=10):
        return {
            "total_events": self.total_events,

            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,

            "duration_seconds": self.duration_seconds(),
            "events_per_second": self.events_per_second(),

            "top_agents": self.agents.most_common(top_n),
            "top_decoders": self.decoders.most_common(top_n),

            "rule_levels": self.rule_levels.most_common(),

            "top_source_ips": self.source_ips.most_common(top_n),
            "top_destination_ips": self.destination_ips.most_common(top_n),
        }
