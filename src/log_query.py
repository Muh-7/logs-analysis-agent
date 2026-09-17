from datetime import datetime
from typing import Callable, Iterator


class LogQuery:

    def __init__(self, log_source: Callable[[], Iterator[dict]]):
        self.log_source = log_source

    def _logs(self):
        return self.log_source()

    def by_agent(self, agent_name: str):
        for log in self._logs():
            if log["agent_name"] == agent_name:
                yield log

    def by_decoder(self, decoder: str):
        for log in self._logs():
            if log["decoder"] == decoder:
                yield log

    def by_source_ip(self, source_ip: str):
        for log in self._logs():
            if log["source_ip"] == source_ip:
                yield log

    def by_rule_level(self, min_level: int):
        for log in self._logs():

            level = log["rule_level"]

            if level is not None and level >= min_level:
                yield log

    def search_message(self, keyword: str):
        keyword = keyword.lower()

        for log in self._logs():

            message = log["message"]

            if message and keyword in message.lower():
                yield log

    def between(
        self,
        start: datetime,
        end: datetime,
    ):
        for log in self._logs():

            timestamp = log["timestamp"]

            if not timestamp:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                continue

            if start <= timestamp <= end:
                yield log