from dataclasses import dataclass


@dataclass
class Event:
    id: str
    title: str


@dataclass
class Campaign:
    id: str
    title: str
