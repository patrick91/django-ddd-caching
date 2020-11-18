from dataclasses import dataclass
from typing import Protocol


@dataclass
class DataFetchingStats:
    number_of_sql_calls: int = 0
    number_of_redis_gets: int = 0
    number_of_redis_sets: int = 0


class WithStats(Protocol):
    stats: DataFetchingStats


def increase_sql_queries(fn):
    def wrap(self, *args, **kwargs):
        self.stats.number_of_sql_calls += 1

        return fn(self, *args, **kwargs)

    return wrap


def increase_redis_sets(fn):
    def wrap(self, *args, **kwargs):
        self.stats.number_of_redis_sets += 1

        return fn(self, *args, **kwargs)

    return wrap


def increase_redis_gets(fn):
    def wrap(self, *args, **kwargs):
        self.stats.number_of_redis_gets += 1

        return fn(self, *args, **kwargs)

    return wrap
