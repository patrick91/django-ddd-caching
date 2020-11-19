from dataclasses import dataclass


@dataclass
class Brand:
    id: str
    name: str


@dataclass
class Event:
    id: str
    title: str
    body: str


@dataclass
class Campaign:
    id: str
    brand_id: str
    title: str
    body: str
